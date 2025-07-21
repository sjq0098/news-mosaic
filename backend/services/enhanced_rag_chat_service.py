"""
增强RAG对话服务 - 基于向量检索的智能新闻问答系统
支持多轮对话、用户记忆、个性化推荐
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
from pydantic import BaseModel, Field

from core.database import get_mongodb_database, Collections
from services.qwen_service import QWENService
from services.embedding_service import QWenEmbeddingService
from services.vector_db_service import get_vector_db
from services.news_service import NewsService
from models.chat import ChatMessage, MessageRole, MessageType


class RAGChatRequest(BaseModel):
    """RAG对话请求"""
    user_id: Optional[str] = Field(None, description="用户ID")
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    # 检索参数
    max_context_news: int = Field(default=5, ge=1, le=10, description="最大上下文新闻数量")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    
    # 生成参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=1000, ge=100, le=2000, description="最大token数")
    
    # 功能选项
    use_user_memory: bool = Field(default=True, description="是否使用用户记忆")
    include_related_news: bool = Field(default=True, description="是否包含相关新闻")
    enable_personalization: bool = Field(default=True, description="是否启用个性化")


class RAGChatResponse(BaseModel):
    """RAG对话响应"""
    success: bool
    message: str
    session_id: str
    
    # 回复内容
    ai_response: str
    confidence_score: float = 0.0
    
    # 上下文信息
    relevant_news: List[Dict[str, Any]] = []
    context_summary: Optional[str] = None
    
    # 元数据
    processing_time: float = 0.0
    tokens_used: int = 0
    sources_count: int = 0
    
    # 推荐
    follow_up_questions: List[str] = []
    related_topics: List[str] = []


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class EnhancedRAGChatService:
    """增强RAG对话服务"""
    
    def __init__(self):
        self.qwen_service = None
        self.embedding_service = None
        self.vector_db = None
        self.news_service = None
        self.db = None
        
        # 对话上下文缓存
        self.conversation_cache: Dict[str, ConversationContext] = {}
        
    async def _initialize_services(self):
        """初始化服务"""
        if not self.qwen_service:
            self.qwen_service = QWENService()
            self.embedding_service = QWenEmbeddingService()
            self.vector_db = get_vector_db()
            self.news_service = NewsService()
            self.db = await get_mongodb_database()
    
    async def chat_with_rag(self, request: RAGChatRequest) -> RAGChatResponse:
        """
        基于RAG的智能对话
        """
        start_time = time.time()
        
        try:
            await self._initialize_services()
            
            # 获取或创建会话
            session_id = request.session_id or str(uuid.uuid4())
            conversation = await self._get_or_create_conversation(session_id, request.user_id)
            
            # 添加用户消息到对话历史
            user_message = ChatMessage(
                session_id=session_id,
                role=MessageRole.USER,
                content=request.message,
                timestamp=datetime.utcnow(),
                message_type=MessageType.TEXT
            )
            conversation.messages.append(user_message)
            
            # 1. 检索相关新闻
            relevant_news = await self._retrieve_relevant_news(
                request.message,
                request.max_context_news,
                request.similarity_threshold,
                request.user_id if request.enable_personalization else None
            )
            
            # 2. 构建上下文
            context = await self._build_conversation_context(
                conversation,
                relevant_news,
                request.use_user_memory,
                request.user_id
            )
            
            # 3. 生成AI回复
            ai_response = await self._generate_ai_response(
                request.message,
                context,
                conversation.messages[-5:],  # 最近5条消息
                request.temperature,
                request.max_tokens
            )
            
            # 4. 添加AI回复到对话历史
            assistant_message = ChatMessage(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=ai_response.content,
                timestamp=datetime.utcnow(),
                message_type=MessageType.TEXT,
                metadata={
                    "tokens_used": ai_response.tokens_used,
                    "sources_count": len(relevant_news)
                }
            )
            conversation.messages.append(assistant_message)
            
            # 5. 更新对话上下文
            await self._update_conversation(conversation)
            
            # 6. 生成后续问题和相关话题
            follow_up_questions = await self._generate_follow_up_questions(
                request.message, ai_response.content, relevant_news
            )
            related_topics = await self._extract_related_topics(relevant_news)
            
            # 7. 计算置信度
            confidence_score = self._calculate_confidence_score(
                relevant_news, ai_response.tokens_used, len(context)
            )
            
            processing_time = time.time() - start_time
            
            return RAGChatResponse(
                success=True,
                message="对话成功",
                session_id=session_id,
                ai_response=ai_response.content,
                confidence_score=confidence_score,
                relevant_news=[self._format_news_for_response(news) for news in relevant_news],
                context_summary=await self._generate_context_summary(relevant_news),
                processing_time=processing_time,
                tokens_used=ai_response.tokens_used,
                sources_count=len(relevant_news),
                follow_up_questions=follow_up_questions,
                related_topics=related_topics
            )
            
        except Exception as e:
            logger.error(f"RAG对话失败: {e}")
            return RAGChatResponse(
                success=False,
                message=f"对话失败: {str(e)}",
                session_id=request.session_id or "error",
                ai_response="抱歉，我现在无法回答您的问题，请稍后再试。",
                processing_time=time.time() - start_time
            )
    
    async def _retrieve_relevant_news(self, query: str, max_results: int,
                                    threshold: float, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """检索相关新闻"""
        try:
            # 先尝试向量数据库检索
            try:
                similar_results = self.vector_db.query_similar(query, top_k=max_results * 2)

                # 过滤低相似度结果
                filtered_results = [
                    result for result in similar_results
                    if result.get("score", 0) >= threshold
                ]

                # 如果启用个性化，根据用户兴趣调整排序
                if user_id:
                    filtered_results = await self._personalize_results(filtered_results, user_id)

                # 获取新闻详细信息
                news_list = []
                for result in filtered_results[:max_results]:
                    news_id = result.get("news_id")
                    if news_id:
                        news = await self.db[Collections.NEWS].find_one({"_id": news_id})
                        if news:
                            news["similarity_score"] = result.get("score", 0)
                            news_list.append(news)

                if news_list:
                    return news_list

            except Exception as vector_error:
                logger.warning(f"向量检索失败，使用文本搜索: {vector_error}")

            # 备用方案：使用文本搜索
            search_terms = query.split()
            search_regex = "|".join(search_terms)

            cursor = self.db[Collections.NEWS].find({
                "$or": [
                    {"title": {"$regex": search_regex, "$options": "i"}},
                    {"content": {"$regex": search_regex, "$options": "i"}},
                    {"snippet": {"$regex": search_regex, "$options": "i"}}
                ]
            }).sort("published_at", -1).limit(max_results)

            news_list = []
            async for news in cursor:
                news["similarity_score"] = 0.8  # 默认相似度
                news_list.append(news)

            return news_list

        except Exception as e:
            logger.error(f"检索相关新闻失败: {e}")
            return []
    
    async def _build_conversation_context(self, conversation: ConversationContext, 
                                        relevant_news: List[Dict[str, Any]], 
                                        use_user_memory: bool, user_id: str) -> str:
        """构建对话上下文"""
        context_parts = []
        
        # 添加相关新闻
        if relevant_news:
            context_parts.append("相关新闻信息：")
            for i, news in enumerate(relevant_news, 1):
                context_parts.append(f"{i}. 标题：{news['title']}")
                context_parts.append(f"   内容：{news.get('content', '')[:200]}...")
                context_parts.append(f"   来源：{news.get('source', '未知')}")
                context_parts.append("")
        
        # 添加用户记忆（如果启用）
        if use_user_memory:
            user_context = await self._get_user_context(user_id)
            if user_context:
                context_parts.append("用户背景信息：")
                context_parts.append(user_context)
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, user_message: str, context: str, 
                                  chat_history: List[ChatMessage], 
                                  temperature: float, max_tokens: int):
        """生成AI回复"""
        # 构建系统提示词
        system_prompt = """
        你是一个专业的新闻分析助手，基于提供的新闻信息回答用户问题。

        回答要求：
        1. 基于提供的新闻信息进行回答
        2. 保持客观中立，避免主观判断
        3. 如果信息不足，诚实说明
        4. 提供具体的事实和数据
        5. 语言简洁清晰，逻辑清楚
        
        上下文信息：
        """ + context
        
        # 构建对话历史
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加最近的对话历史
        for msg in chat_history[-3:]:  # 最近3条消息
            messages.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.content
            })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用QWEN API
        api_response = await self.qwen_service._call_qwen_api(
            messages, temperature, max_tokens
        )

        # 包装为QWENResponse对象
        from services.qwen_service import QWENResponse
        return QWENResponse(
            content=api_response.get("content", "抱歉，我无法生成回复。"),
            tokens_used=api_response.get("tokens_used", 0),
            generation_time=0.0,
            news_ids=[]
        )

    async def _get_or_create_conversation(self, session_id: str, user_id: str) -> ConversationContext:
        """获取或创建对话上下文"""
        # 先从缓存中查找
        if session_id in self.conversation_cache:
            conversation = self.conversation_cache[session_id]
            conversation.updated_at = datetime.utcnow()
            return conversation

        # 从数据库中查找
        try:
            conversation_doc = await self.db[Collections.CONVERSATIONS].find_one({
                "session_id": session_id,
                "user_id": user_id
            })

            if conversation_doc:
                # 重建对话对象
                messages = [
                    ChatMessage(**msg) for msg in conversation_doc.get("messages", [])
                ]
                conversation = ConversationContext(
                    session_id=session_id,
                    user_id=user_id,
                    messages=messages,
                    created_at=conversation_doc["created_at"],
                    updated_at=datetime.utcnow(),
                    metadata=conversation_doc.get("metadata", {})
                )
            else:
                # 创建新对话
                conversation = ConversationContext(
                    session_id=session_id,
                    user_id=user_id,
                    messages=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata={}
                )

            # 添加到缓存
            self.conversation_cache[session_id] = conversation
            return conversation

        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            # 返回新对话
            return ConversationContext(
                session_id=session_id,
                user_id=user_id,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={}
            )

    async def _update_conversation(self, conversation: ConversationContext):
        """更新对话上下文"""
        try:
            conversation_doc = {
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "messages": [msg.__dict__ for msg in conversation.messages],
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "metadata": conversation.metadata
            }

            await self.db[Collections.CONVERSATIONS].replace_one(
                {"session_id": conversation.session_id, "user_id": conversation.user_id},
                conversation_doc,
                upsert=True
            )

            # 更新缓存
            self.conversation_cache[conversation.session_id] = conversation

        except Exception as e:
            logger.error(f"更新对话上下文失败: {e}")

    async def _get_user_context(self, user_id: str) -> Optional[str]:
        """获取用户上下文信息"""
        try:
            # 获取用户兴趣
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs:
                return None

            interests = user_prefs.get("interests", {})
            if not interests:
                return None

            # 获取最感兴趣的话题
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:5]
            interest_text = "、".join([interest for interest, _ in top_interests])

            return f"用户主要关注：{interest_text}"

        except Exception as e:
            logger.error(f"获取用户上下文失败: {e}")
            return None

    async def _personalize_results(self, results: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """个性化结果排序"""
        try:
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs or not user_prefs.get("interests"):
                return results

            interests = user_prefs["interests"]

            # 为每个结果计算个性化分数
            for result in results:
                news_id = result.get("news_id")
                if news_id:
                    news = await self.db[Collections.NEWS].find_one({"_id": news_id})
                    if news:
                        # 简单的个性化评分：基于标题和内容中的关键词匹配
                        text = f"{news.get('title', '')} {news.get('content', '')}".lower()
                        interest_score = 0
                        for interest, weight in interests.items():
                            if interest.lower() in text:
                                interest_score += weight

                        # 结合原始相似度分数和兴趣分数
                        original_score = result.get("score", 0)
                        personalized_score = original_score * 0.7 + (interest_score / 100) * 0.3
                        result["score"] = personalized_score

            # 重新排序
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results

        except Exception as e:
            logger.error(f"个性化结果失败: {e}")
            return results

    async def _generate_follow_up_questions(self, user_message: str, ai_response: str,
                                          relevant_news: List[Dict[str, Any]]) -> List[str]:
        """生成后续问题"""
        try:
            # 基于新闻内容生成相关问题
            questions = []

            # 从新闻中提取关键主题
            topics = set()
            for news in relevant_news[:3]:
                title = news.get("title", "")
                # 简单的关键词提取
                words = title.split()
                for word in words:
                    if len(word) > 2:
                        topics.add(word)

            # 生成问题模板
            question_templates = [
                "关于{}的最新发展如何？",
                "{}对相关行业有什么影响？",
                "{}的背景是什么？",
                "{}未来的趋势如何？"
            ]

            for topic in list(topics)[:2]:
                for template in question_templates[:2]:
                    questions.append(template.format(topic))

            return questions[:4]  # 最多返回4个问题

        except Exception as e:
            logger.error(f"生成后续问题失败: {e}")
            return ["还有其他相关问题吗？", "您想了解更多详情吗？"]

    async def _extract_related_topics(self, relevant_news: List[Dict[str, Any]]) -> List[str]:
        """提取相关话题"""
        try:
            topics = set()

            for news in relevant_news:
                # 从标题中提取关键词
                title = news.get("title", "")
                words = title.split()
                for word in words:
                    if len(word) > 2 and word.isalpha():
                        topics.add(word)

                # 从分类中提取
                category = news.get("category")
                if category:
                    topics.add(category)

            return list(topics)[:8]  # 最多返回8个话题

        except Exception as e:
            logger.error(f"提取相关话题失败: {e}")
            return []

    def _calculate_confidence_score(self, relevant_news: List[Dict[str, Any]],
                                  tokens_used: int, context_length: int) -> float:
        """计算置信度分数"""
        try:
            # 基于多个因素计算置信度
            base_score = 0.5

            # 相关新闻数量因子
            news_factor = min(len(relevant_news) / 5.0, 1.0) * 0.3

            # 相似度因子
            if relevant_news:
                avg_similarity = sum(news.get("similarity_score", 0) for news in relevant_news) / len(relevant_news)
                similarity_factor = avg_similarity * 0.3
            else:
                similarity_factor = 0

            # 上下文长度因子
            context_factor = min(context_length / 1000.0, 1.0) * 0.2

            confidence = base_score + news_factor + similarity_factor + context_factor
            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return 0.5

    def _format_news_for_response(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """格式化新闻用于响应"""
        return {
            "id": news.get("_id"),
            "title": news.get("title"),
            "content": news.get("content", "")[:200] + "..." if len(news.get("content", "")) > 200 else news.get("content", ""),
            "url": news.get("url"),
            "source": news.get("source"),
            "published_at": news.get("published_at"),
            "similarity_score": news.get("similarity_score", 0)
        }

    async def _generate_context_summary(self, relevant_news: List[Dict[str, Any]]) -> Optional[str]:
        """生成上下文摘要"""
        if not relevant_news:
            return None

        try:
            # 简单的摘要生成
            sources = set(news.get("source", "未知") for news in relevant_news)
            topics = set()

            for news in relevant_news:
                title_words = news.get("title", "").split()
                topics.update(word for word in title_words if len(word) > 2)

            summary = f"基于{len(relevant_news)}条来自{len(sources)}个来源的新闻，主要涉及：{', '.join(list(topics)[:5])}"
            return summary

        except Exception as e:
            logger.error(f"生成上下文摘要失败: {e}")
            return None


# 全局实例
enhanced_rag_chat_service = EnhancedRAGChatService()


async def get_enhanced_rag_chat_service() -> EnhancedRAGChatService:
    """获取增强RAG对话服务实例"""
    return enhanced_rag_chat_service
