"""
增强对话服务 - 集成RAG、用户记忆和个性化回复
"""

import uuid
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

from pydantic import BaseModel, Field
from models.chat import ChatMessage, MessageRole, MessageType
from models.user_memory import MemoryType, InterestCategory, MemoryQueryRequest
from models.news import NewsModel
from services.qwen_service import QWENService
from services.embedding_service import QWenEmbeddingService
from services.conversation_context_manager import ConversationContextManager, context_manager
from services.integrated_rag_service import IntegratedRAGService
from mock_data.news_samples import mock_news_db


class EnhancedChatRequest(BaseModel):
    """增强对话请求"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    
    # 可选的上下文信息
    include_memory: bool = Field(default=True, description="是否包含用户记忆")
    include_rag: bool = Field(default=True, description="是否使用RAG检索")
    include_news_card: bool = Field(default=False, description="是否生成新闻卡片")
    
    # 个性化选项
    response_style: Optional[str] = Field(None, description="回复风格偏好")
    max_context_memories: int = Field(default=5, description="最大上下文记忆数")


class EnhancedChatResponse(BaseModel):
    """增强对话响应"""
    session_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")
    
    # 回复内容
    response: str = Field(..., description="AI回复内容")
    response_type: MessageType = Field(default=MessageType.TEXT, description="回复类型")
    
    # 上下文信息
    used_memories_count: int = Field(default=0, description="使用的记忆数量")
    used_news_count: int = Field(default=0, description="使用的新闻数量")
    personalization_applied: bool = Field(default=False, description="是否应用了个性化")
    
    # 可选的新闻卡片
    news_card: Optional[Any] = Field(None, description="生成的新闻卡片")
    
    # 元数据
    processing_time_ms: float = Field(..., description="处理时间（毫秒）")
    confidence_score: float = Field(default=0.8, description="回复置信度")
    context_summary: str = Field(..., description="上下文摘要")
    
    # 推荐信息
    suggested_topics: List[str] = Field(default_factory=list, description="推荐话题")
    related_news: List[Dict[str, Any]] = Field(default_factory=list, description="相关新闻")


class EnhancedChatService:
    """增强对话服务"""
    
    def __init__(self):
        self.qwen_service = QWENService()
        self.embedding_service = QWenEmbeddingService()
        self.context_manager = context_manager
        self.rag_service = IntegratedRAGService()
        
        # 对话历史存储 (生产环境中应使用数据库)
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        logger.info("增强对话服务已初始化")
    
    async def initialize(self):
        """初始化服务"""
        try:
            # 初始化RAG服务
            await self.rag_service.initialize_pipeline()
            logger.info("增强对话服务初始化完成")
        except Exception as e:
            logger.error(f"增强对话服务初始化失败: {e}")
            raise
    
    async def chat_with_enhanced_context(
        self, 
        request: EnhancedChatRequest
    ) -> EnhancedChatResponse:
        """带增强上下文的对话"""
        start_time = time.time()
        
        try:
            # 创建用户消息
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=request.session_id,
                role=MessageRole.USER,
                content=request.message,
                metadata={"user_id": request.user_id}
            )
            
            # 添加到对话历史
            self._add_to_conversation_history(request.session_id, user_message)
            
            # 获取增强上下文
            enhanced_context = await self._gather_enhanced_context(
                user_id=request.user_id,
                session_id=request.session_id,
                query=request.message,
                include_memory=request.include_memory,
                include_rag=request.include_rag,
                max_context_memories=request.max_context_memories
            )
            
            # 生成个性化提示词
            personalized_prompt = await self._create_personalized_prompt(
                user_message=request.message,
                context=enhanced_context,
                user_id=request.user_id,
                response_style=request.response_style
            )
            
            # 生成AI回复
            ai_response_obj = await self.qwen_service.generate_response(
                user_message=personalized_prompt,
                max_tokens=1000,
                temperature=0.7,
                include_news=False  # 我们已经在RAG流程中处理了新闻
            )
            ai_response = ai_response_obj.content
            
            # 创建AI消息
            ai_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=request.session_id,
                role=MessageRole.ASSISTANT,
                content=ai_response,
                metadata={
                    "context_used": enhanced_context.get("context_summary", ""),
                    "personalized": enhanced_context.get("personalized", False)
                }
            )
            
            # 添加到对话历史
            self._add_to_conversation_history(request.session_id, ai_message)
            
            # 更新对话上下文
            await self._update_conversation_context(
                session_id=request.session_id,
                user_message=user_message,
                ai_message=ai_message,
                extracted_info=enhanced_context
            )
            
            # 保存新的记忆
            await self._save_conversation_memory(
                user_id=request.user_id,
                user_message=request.message,
                ai_response=ai_response,
                context=enhanced_context
            )
            
            # 生成新闻卡片 (如果需要)
            news_card = None
            if request.include_news_card and enhanced_context.get("relevant_news"):
                try:
                    news_card = await self.rag_service.generate_news_card(request.message)
                except Exception as e:
                    logger.warning(f"生成新闻卡片失败: {e}")
            
            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000
            
            # 构建响应
            response = EnhancedChatResponse(
                session_id=request.session_id,
                message_id=ai_message.id,
                response=ai_response,
                used_memories_count=len(enhanced_context.get("relevant_memories", [])),
                used_news_count=len(enhanced_context.get("relevant_news", [])),
                personalization_applied=enhanced_context.get("personalization_applied", False),
                news_card=news_card,
                processing_time_ms=processing_time,
                context_summary=enhanced_context.get("context_summary", ""),
                suggested_topics=enhanced_context.get("suggested_topics", []),
                related_news=enhanced_context.get("related_news", [])
            )
            
            logger.info(f"增强对话完成，用户: {request.user_id}, 耗时: {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"增强对话处理失败: {e}")
            raise
    
    async def _gather_enhanced_context(
        self,
        user_id: str,
        session_id: str,
        query: str,
        include_memory: bool = True,
        include_rag: bool = True,
        max_context_memories: int = 5
    ) -> Dict[str, Any]:
        """收集增强上下文信息"""
        context = {
            "user_preferences": None,
            "relevant_memories": [],
            "relevant_news": [],
            "conversation_context": None,
            "context_summary": "",
            "personalization_applied": False,
            "suggested_topics": [],
            "related_news": []
        }
        
        try:
            # 获取基础上下文
            if include_memory:
                basic_context = await self.context_manager.get_relevant_context(
                    user_id=user_id,
                    current_query=query,
                    session_id=session_id
                )
                context.update(basic_context)
            
            # 获取RAG相关新闻
            if include_rag:
                try:
                    rag_news = await self.rag_service.search_relevant_news(query, top_k=3)
                    context["relevant_news"] = rag_news
                    context["related_news"] = [
                        {
                            "title": news.get("title", ""),
                            "source": news.get("source", ""),
                            "category": news.get("category", ""),
                            "similarity": news.get("similarity", 0.0)
                        }
                        for news in rag_news
                    ]
                except Exception as e:
                    logger.warning(f"RAG检索失败: {e}")
            
            # 生成上下文摘要
            context["context_summary"] = self._generate_context_summary(context)
            
            # 应用个性化
            if context.get("user_preferences"):
                context["personalization_applied"] = True
                context["suggested_topics"] = self._generate_suggested_topics(
                    user_preferences=context["user_preferences"],
                    current_query=query
                )
            
            return context
            
        except Exception as e:
            logger.error(f"收集增强上下文失败: {e}")
            return context
    
    async def _create_personalized_prompt(
        self,
        user_message: str,
        context: Dict[str, Any],
        user_id: str,
        response_style: Optional[str] = None
    ) -> str:
        """创建个性化提示词"""
        
        # 基础提示词
        base_prompt = f"""你是一个智能新闻分析助手，具有强大的RAG检索能力和个性化服务功能。

用户问题: {user_message}

"""
        
        # 添加用户偏好信息
        if context.get("user_preferences"):
            prefs = context["user_preferences"]
            base_prompt += f"""
用户偏好信息:
- 偏好分类: {', '.join([cat.value for cat in prefs.preferred_categories]) if prefs.preferred_categories else '无特定偏好'}
- 沟通风格: {prefs.communication_style}
- 回复格式: {prefs.response_format}
- 分析深度: {prefs.preferred_analysis_depth}

"""
        
        # 添加相关记忆
        if context.get("relevant_memories"):
            memories = context["relevant_memories"][:3]  # 最多使用3条记忆
            memory_text = "\n".join([f"- {mem.content[:100]}..." for mem in memories])
            base_prompt += f"""
相关历史记忆:
{memory_text}

"""
        
        # 添加RAG检索到的新闻
        if context.get("relevant_news"):
            news_list = context["relevant_news"][:2]  # 最多使用2条新闻
            news_text = "\n".join([
                f"- 【{news.get('category', '未知')}】{news.get('title', '')} (来源: {news.get('source', '未知')})"
                for news in news_list
            ])
            base_prompt += f"""
相关新闻信息:
{news_text}

"""
        
        # 添加对话上下文
        if context.get("conversation_context"):
            conv_context = context["conversation_context"]
            if conv_context.current_topic:
                base_prompt += f"""
当前对话话题: {conv_context.current_topic}
已讨论话题: {', '.join(conv_context.discussed_topics[-3:]) if conv_context.discussed_topics else '无'}

"""
        
        # 个性化回复要求
        style_instruction = ""
        if response_style:
            style_instruction = f"请以{response_style}风格回复。"
        elif context.get("user_preferences"):
            prefs = context["user_preferences"]
            if prefs.communication_style == "casual":
                style_instruction = "请以轻松、友好的语调回复。"
            elif prefs.communication_style == "academic":
                style_instruction = "请以学术、专业的方式回复。"
            else:
                style_instruction = "请以专业、清晰的方式回复。"
            
            if prefs.response_format == "structured":
                style_instruction += "回复请使用结构化格式，包含要点分析。"
            elif prefs.response_format == "detailed":
                style_instruction += "请提供详细、全面的分析。"
        
        base_prompt += f"""
回复要求:
1. {style_instruction}
2. 基于提供的新闻信息和历史记忆，给出准确、有价值的回复
3. 如果有相关新闻，请结合新闻内容进行分析
4. 保持回复的连贯性和个性化
5. 如果用户询问之前讨论过的内容，请参考历史记忆

请生成高质量的个性化回复:"""
        
        return base_prompt
    
    async def _update_conversation_context(
        self,
        session_id: str,
        user_message: ChatMessage,
        ai_message: ChatMessage,
        extracted_info: Dict[str, Any]
    ):
        """更新对话上下文"""
        try:
            # 提取话题和实体 (简化版本)
            topics = self._extract_topics_from_message(user_message.content)
            entities = self._extract_entities_from_message(user_message.content)
            
            # 更新用户消息上下文
            await self.context_manager.update_conversation_context(
                session_id=session_id,
                message=user_message,
                extracted_topics=topics,
                mentioned_entities=entities
            )
            
            # 更新AI消息上下文
            await self.context_manager.update_conversation_context(
                session_id=session_id,
                message=ai_message,
                extracted_topics=topics,
                mentioned_entities=entities
            )
            
        except Exception as e:
            logger.error(f"更新对话上下文失败: {e}")
    
    async def _save_conversation_memory(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        context: Dict[str, Any]
    ):
        """保存对话记忆"""
        try:
            # 保存交互记忆
            interaction_content = f"用户问: {user_message[:100]}... | AI答: {ai_response[:100]}..."
            await self.context_manager.add_memory(
                user_id=user_id,
                content=interaction_content,
                memory_type=MemoryType.INTERACTION,
                context={
                    "full_question": user_message,
                    "full_answer": ai_response,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_summary": context.get("context_summary", "")
                },
                importance_score=0.6,
                related_topics=self._extract_topics_from_message(user_message)
            )
            
            # 如果涉及新闻，保存相关记忆
            if context.get("relevant_news"):
                news_titles = [news.get("title", "") for news in context["relevant_news"][:2]]
                news_memory = f"讨论了关于 {', '.join(news_titles)} 的新闻内容"
                await self.context_manager.add_memory(
                    user_id=user_id,
                    content=news_memory,
                    memory_type=MemoryType.FACT,
                    context={"news_titles": news_titles},
                    importance_score=0.7
                )
            
        except Exception as e:
            logger.error(f"保存对话记忆失败: {e}")
    
    def _add_to_conversation_history(self, session_id: str, message: ChatMessage):
        """添加消息到对话历史"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append(message)
        
        # 保持历史记录在合理范围内
        if len(self.conversation_history[session_id]) > 50:
            self.conversation_history[session_id] = self.conversation_history[session_id][-50:]
    
    def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """生成上下文摘要"""
        summary_parts = []
        
        if context.get("relevant_memories"):
            summary_parts.append(f"使用了 {len(context['relevant_memories'])} 条用户记忆")
        
        if context.get("relevant_news"):
            summary_parts.append(f"检索到 {len(context['relevant_news'])} 条相关新闻")
        
        if context.get("conversation_context"):
            conv_context = context["conversation_context"]
            if conv_context.current_topic:
                summary_parts.append(f"当前话题: {conv_context.current_topic}")
        
        if context.get("personalization_applied"):
            summary_parts.append("应用了个性化设置")
        
        return "; ".join(summary_parts) if summary_parts else "基础对话模式"
    
    def _generate_suggested_topics(
        self, 
        user_preferences: Any, 
        current_query: str
    ) -> List[str]:
        """生成推荐话题"""
        suggestions = []
        
        # 基于用户偏好生成建议
        if user_preferences.preferred_categories:
            for category in user_preferences.preferred_categories[:2]:
                if category == InterestCategory.TECHNOLOGY:
                    suggestions.extend(["AI技术发展", "科技创新趋势"])
                elif category == InterestCategory.FINANCE:
                    suggestions.extend(["经济形势分析", "投资理财建议"])
                elif category == InterestCategory.EDUCATION:
                    suggestions.extend(["教育政策解读", "学习方法分享"])
        
        # 基于当前查询生成相关建议
        if "AI" in current_query or "人工智能" in current_query:
            suggestions.append("AI应用前景")
        
        if "经济" in current_query or "市场" in current_query:
            suggestions.append("市场趋势分析")
        
        return list(set(suggestions))[:3]  # 去重并限制数量
    
    def _extract_topics_from_message(self, message: str) -> List[str]:
        """从消息中提取话题 (简化版本)"""
        topics = []
        
        # 简单的关键词提取
        if "AI" in message or "人工智能" in message:
            topics.append("人工智能")
        if "经济" in message or "市场" in message:
            topics.append("经济市场")
        if "新能源" in message:
            topics.append("新能源")
        if "教育" in message:
            topics.append("教育")
        if "科技" in message:
            topics.append("科技")
        
        return topics
    
    def _extract_entities_from_message(self, message: str) -> List[str]:
        """从消息中提取实体 (简化版本)"""
        entities = []
        
        # 简单的实体识别
        companies = ["比亚迪", "特斯拉", "理想汽车", "微软", "苹果", "谷歌"]
        for company in companies:
            if company in message:
                entities.append(company)
        
        return entities
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[ChatMessage]:
        """获取对话历史"""
        history = self.conversation_history.get(session_id, [])
        return history[-limit:] if history else []
    
    async def clear_conversation_history(self, session_id: str):
        """清空对话历史"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        
        # 清理对话上下文
        if session_id in self.context_manager.active_contexts:
            del self.context_manager.active_contexts[session_id]
        
        logger.info(f"已清空会话 {session_id} 的对话历史")


# 创建全局实例
enhanced_chat_service = EnhancedChatService() 