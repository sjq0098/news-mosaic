"""
新闻对话服务 - 结合RAG增强的新闻分析与智能对话
"""

import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json
import logging
import hashlib

from models.chat import (
    ChatSession, ChatMessage, ChatMessageCreate, ChatSessionCreate,
    MessageRole, MessageType, ChatStatus
)
from models.news import NewsModel, NewsCategory
from models.news_card import NewsCard, NewsCardMetadata
from services.rag_enhanced_card_service import RAGEnhancedCardService
from services.qwen_service import QWENService, QWENResponse
from services.vector_db_service import get_vector_db
from core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class NewsConversationContext:
    """新闻对话上下文"""
    news_cards: List[NewsCard]  # 已分析的新闻卡片
    current_news: Optional[NewsModel] = None  # 当前讨论的新闻
    user_interests: List[str] = None  # 用户兴趣点
    conversation_theme: str = ""  # 对话主题
    follow_up_questions: List[str] = None  # 建议的追问
    
    def __post_init__(self):
        if self.user_interests is None:
            self.user_interests = []
        if self.follow_up_questions is None:
            self.follow_up_questions = []


class NewsChatService:
    """新闻对话服务"""
    
    def __init__(self):
        self.rag_card_service = RAGEnhancedCardService()
        self.qwen_service = QWENService()
        self.vector_db = get_vector_db()
        
        # 会话存储（实际应用中应该使用数据库）
        self._sessions: Dict[str, ChatSession] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._contexts: Dict[str, NewsConversationContext] = {}
    
    async def create_news_session(
        self,
        user_id: str,
        initial_news: Optional[NewsModel] = None,
        session_title: Optional[str] = None
    ) -> ChatSession:
        """创建新闻对话会话"""
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=session_title or "新闻分析对话",
            status=ChatStatus.ACTIVE,
            created_at=datetime.utcnow(),
            metadata={
                "type": "news_chat",
                "initial_news_id": initial_news.id if initial_news else None
            }
        )
        
        self._sessions[session_id] = session
        self._messages[session_id] = []
        self._contexts[session_id] = NewsConversationContext(news_cards=[])
        
        # 如果有初始新闻，进行分析并欢迎
        if initial_news:
            await self._process_initial_news(session_id, initial_news)
        
        return session
    
    async def send_news_message(
        self,
        session_id: str,
        user_message: str,
        news_data: Optional[NewsModel] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """发送新闻相关消息并获取智能回复"""
        
        if session_id not in self._sessions:
            raise ValueError(f"会话 {session_id} 不存在")
        
        context = self._contexts[session_id]
        
        # 添加用户消息
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            message_type=MessageType.TEXT,
            created_at=datetime.utcnow()
        )
        self._messages[session_id].append(user_msg)
        
        # 处理不同类型的输入
        if news_data:
            # 用户提供了新新闻
            response = await self._handle_new_news(session_id, news_data, user_message)
        else:
            # 用户的追问或讨论
            response = await self._handle_follow_up(session_id, user_message)
        
        # 添加AI回复消息
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response["content"],
            message_type=response.get("message_type", MessageType.TEXT),
            metadata=response.get("metadata", {}),
            created_at=datetime.utcnow()
        )
        self._messages[session_id].append(assistant_msg)
        
        return {
            "user_message": user_msg.model_dump(),
            "assistant_message": assistant_msg.model_dump(),
            "conversation_context": self._get_context_summary(session_id),
            "suggested_questions": response.get("suggested_questions", [])
        }
    
    async def _process_initial_news(self, session_id: str, news: NewsModel):
        """处理初始新闻"""
        context = self._contexts[session_id]
        
        # 生成新闻卡片
        from models.news_card import NewsCardRequest
        request = NewsCardRequest(
            news_id=news.id or f"temp_{hashlib.md5(news.title.encode()).hexdigest()[:8]}",
            include_sentiment=True,
            include_entities=True,
            include_related=True
        )
        response = await self.rag_card_service.generate_card_with_rag(news, request)
        news_card = response.card
        context.news_cards.append(news_card)
        context.current_news = news
        
        # 生成欢迎消息
        welcome_message = await self._generate_welcome_message(news_card)
        
        welcome_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=welcome_message["content"],
            message_type=MessageType.NEWS_CARD,
            metadata={
                "news_card": news_card.model_dump(),
                "suggested_questions": welcome_message["suggested_questions"]
            },
            created_at=datetime.utcnow()
        )
        
        self._messages[session_id].append(welcome_msg)
    
    async def _handle_new_news(
        self,
        session_id: str,
        news: NewsModel,
        user_message: str
    ) -> Dict[str, Any]:
        """处理新提供的新闻"""
        context = self._contexts[session_id]
        
        # 生成新闻卡片
        from models.news_card import NewsCardRequest
        request = NewsCardRequest(
            news_id=news.id or f"temp_{hashlib.md5(news.title.encode()).hexdigest()[:8]}",
            include_sentiment=True,
            include_entities=True,
            include_related=True
        )
        response = await self.rag_card_service.generate_card_with_rag(news, request)
        news_card = response.card
        context.news_cards.append(news_card)
        context.current_news = news
        
        # 分析用户的意图和兴趣
        user_intent = await self._analyze_user_intent(user_message, news_card)
        
        # 生成针对性回复
        response = await self._generate_news_analysis_response(
            news_card, user_message, user_intent, context
        )
        
        return response
    
    async def _handle_follow_up(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """处理用户的追问"""
        context = self._contexts[session_id]
        conversation_history = self._get_recent_messages(session_id, limit=10)
        
        # 分析追问类型
        follow_up_type = await self._analyze_follow_up_type(user_message, context)
        
        # 根据追问类型生成回复
        if follow_up_type == "detail_request":
            response = await self._provide_detailed_analysis(user_message, context)
        elif follow_up_type == "comparison":
            response = await self._provide_comparison_analysis(user_message, context)
        elif follow_up_type == "prediction":
            response = await self._provide_trend_prediction(user_message, context)
        elif follow_up_type == "related_news":
            response = await self._find_related_news(user_message, context)
        else:
            response = await self._generate_general_response(
                user_message, context, conversation_history
            )
        
        return response
    
    async def _generate_welcome_message(self, news_card: NewsCard) -> Dict[str, Any]:
        """生成欢迎消息"""
        
        prompt = f"""
基于以下新闻卡片信息，生成一个友好的欢迎消息，向用户介绍这条新闻的核心信息。

新闻标题: {news_card.title}
新闻摘要: {news_card.metadata.summary}
情感分析: {news_card.metadata.sentiment_label.value} (置信度: {news_card.metadata.sentiment_confidence.value})
重要性评分: {news_card.metadata.importance_score}
主要主题: {news_card.metadata.themes.primary_theme}

要求：
1. 用友好、专业的语调
2. 突出新闻的核心价值和意义
3. 提及情感倾向和重要性
4. 长度控制在150字左右
5. 激发用户的进一步讨论兴趣

请用中文回复。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=300
        )
        
        # 生成建议问题
        suggested_questions = await self._generate_suggested_questions(news_card)
        
        return {
            "content": qwen_response.content,
            "suggested_questions": suggested_questions,
            "message_type": MessageType.NEWS_CARD
        }
    
    async def _generate_suggested_questions(self, news_card: NewsCard) -> List[str]:
        """生成建议的追问问题"""
        
        prompt = f"""
基于以下新闻信息，生成5个用户可能感兴趣的追问问题：

标题: {news_card.title}
摘要: {news_card.metadata.summary}
关键词: {', '.join(news_card.metadata.keywords)}
主题: {news_card.metadata.themes.primary_theme}

生成的问题应该：
1. 涵盖不同角度（影响、原因、趋势、相关性等）
2. 简洁明了，容易理解
3. 能引发深度讨论
4. 符合中文表达习惯

请直接返回5个问题，每行一个，不要编号。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=200
        )
        
        questions = [q.strip() for q in qwen_response.content.split('\n') if q.strip()]
        return questions[:5]
    
    async def _analyze_user_intent(
        self,
        user_message: str,
        news_card: NewsCard
    ) -> Dict[str, Any]:
        """分析用户意图"""
        
        prompt = f"""
分析用户对这条新闻的意图和兴趣点：

新闻: {news_card.title}
用户消息: {user_message}

请分析：
1. 用户的主要关注点
2. 期望的信息深度（概览/详细/专业）
3. 特定兴趣领域
4. 情感态度（关心/质疑/好奇等）

以JSON格式回复：
{{"main_interest": "string", "depth_level": "string", "specific_areas": ["string"], "emotional_attitude": "string"}}
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=150
        )
        
        try:
            return json.loads(qwen_response.content)
        except:
            return {
                "main_interest": "general",
                "depth_level": "moderate",
                "specific_areas": [],
                "emotional_attitude": "curious"
            }
    
    async def _generate_news_analysis_response(
        self,
        news_card: NewsCard,
        user_message: str,
        user_intent: Dict[str, Any],
        context: NewsConversationContext
    ) -> Dict[str, Any]:
        """生成新闻分析回复"""
        
        # 构建历史上下文
        historical_context = ""
        if context.news_cards:
            historical_context = f"相关历史新闻数量: {len(context.news_cards)}"
        
        prompt = f"""
作为新闻分析助手，基于以下信息为用户提供深度分析：

当前新闻: {news_card.title}
新闻摘要: {news_card.metadata.summary}
用户消息: {user_message}
用户兴趣: {user_intent}

新闻深度分析:
- 情感倾向: {news_card.metadata.sentiment_label.value} (分数: {news_card.metadata.sentiment_score})
- 重要性评分: {news_card.metadata.importance_score}/5
- 可信度评估: {news_card.metadata.credibility_level.value} (分数: {news_card.metadata.credibility_score})
- 主要实体: {', '.join([e.entity for e in news_card.metadata.entities])}
- 核心主题: {news_card.metadata.themes.primary_theme}
- 紧急程度: {news_card.metadata.urgency_score}/10

{historical_context}

请提供：
1. 针对用户关注点的专业分析
2. 结合RAG检索到的历史信息的深度解读
3. 这条新闻的更广泛影响和意义
4. 与历史事件的关联性分析

要求：
- 专业但易懂
- 结构清晰
- 200-300字
- 体现深度分析价值
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=500
        )
        
        # 生成新的建议问题
        suggested_questions = await self._generate_contextual_questions(
            news_card, user_message, context
        )
        
        return {
            "content": qwen_response.content,
            "message_type": MessageType.TEXT,
            "metadata": {
                "analysis_type": "comprehensive",
                "news_card_id": news_card.id
            },
            "suggested_questions": suggested_questions
        }
    
    async def _analyze_follow_up_type(
        self,
        user_message: str,
        context: NewsConversationContext
    ) -> str:
        """分析追问类型"""
        
        keywords_map = {
            "detail_request": ["详细", "具体", "深入", "更多", "解释"],
            "comparison": ["比较", "对比", "差别", "相似", "不同"],
            "prediction": ["预测", "未来", "趋势", "发展", "影响"],
            "related_news": ["相关", "类似", "其他", "还有"]
        }
        
        user_lower = user_message.lower()
        
        for follow_type, keywords in keywords_map.items():
            if any(keyword in user_lower for keyword in keywords):
                return follow_type
        
        return "general"
    
    async def _provide_detailed_analysis(
        self,
        user_message: str,
        context: NewsConversationContext
    ) -> Dict[str, Any]:
        """提供详细分析"""
        
        current_card = context.news_cards[-1] if context.news_cards else None
        if not current_card:
            return {"content": "抱歉，我需要先分析一条新闻才能提供详细信息。"}
        
        prompt = f"""
用户想了解更多详细信息: {user_message}

当前新闻卡片完整信息:
{json.dumps(current_card.model_dump(), ensure_ascii=False, indent=2)}

请提供详细的专业分析，包括：
1. 事件的深层原因和背景
2. 涉及的关键技术/政策/经济因素
3. 对不同群体的具体影响
4. 历史对比和发展脉络
5. 专业视角的解读

要求详细但结构化，300-400字。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=600
        )
        
        return {
            "content": qwen_response.content,
            "message_type": MessageType.TEXT,
            "metadata": {"analysis_type": "detailed"}
        }
    
    async def _provide_comparison_analysis(
        self,
        user_message: str,
        context: NewsConversationContext
    ) -> Dict[str, Any]:
        """提供对比分析"""
        
        if len(context.news_cards) < 2:
            return {
                "content": "要进行对比分析，我需要至少两条新闻。请提供另一条新闻或询问相关历史事件的对比。"
            }
        
        # 使用最近的两条新闻进行对比
        recent_cards = context.news_cards[-2:]
        
        prompt = f"""
用户请求对比分析: {user_message}

新闻1: {recent_cards[0].title}
分析1: {recent_cards[0].metadata.model_dump()}

新闻2: {recent_cards[1].title}  
分析2: {recent_cards[1].metadata.model_dump()}

请提供深度对比分析：
1. 事件性质和影响范围的异同
2. 情感倾向和公众反应对比
3. 重要性和影响力差异
4. 发展趋势的相似性和差异性
5. 对未来的不同预示

要求客观、准确、有洞察力，250-350字。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=500
        )
        
        return {
            "content": qwen_response.content,
            "message_type": MessageType.TEXT,
            "metadata": {"analysis_type": "comparison"}
        }
    
    async def _provide_trend_prediction(
        self,
        user_message: str,
        context: NewsConversationContext
    ) -> Dict[str, Any]:
        """提供趋势预测分析"""
        
        current_card = context.news_cards[-1] if context.news_cards else None
        if not current_card:
            return {"content": "请先提供一条新闻，我来为您分析发展趋势。"}
        
        prompt = f"""
用户询问趋势预测: {user_message}

基于当前新闻分析:
新闻: {current_card.title}
紧急程度: {current_card.metadata.urgency_score}/10
重要性: {current_card.metadata.importance_score}/5
关键词: {', '.join(current_card.metadata.keywords)}
主题: {current_card.metadata.themes.primary_theme}

请提供专业的趋势预测分析：
1. 短期发展趋势（1-3个月）
2. 中期影响预测（3-12个月）
3. 长期演进方向（1-3年）
4. 影响因素分析
5. 不确定性和风险评估

要求：
- 基于数据和逻辑推理
- 客观中立，避免过度乐观或悲观
- 结构清晰，300-400字
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=600
        )
        
        return {
            "content": qwen_response.content,
            "message_type": MessageType.TEXT,
            "metadata": {"analysis_type": "trend_prediction"}
        }
    
    async def _find_related_news(
        self,
        user_message: str,
        context: NewsConversationContext
    ) -> Dict[str, Any]:
        """查找相关新闻"""
        
        current_news = context.current_news
        if not current_news:
            return {"content": "请先提供一条新闻，我来为您查找相关内容。"}
        
        # 使用向量检索查找相关新闻
        try:
            related_results = self.vector_db.query_similar(
                query_text=current_news.title + " " + (current_news.summary or ""),
                top_k=5
            )
            
            prompt = f"""
基于用户请求: {user_message}
当前新闻: {current_news.title}

找到的相关新闻:
{json.dumps(related_results, ensure_ascii=False, indent=2)}

请整理并介绍这些相关新闻，说明：
1. 与当前新闻的关联性
2. 时间发展脉络
3. 相关性强弱排序
4. 各自的独特价值

用清晰的结构化方式呈现，200-300字。
"""
            
            qwen_response = await self.qwen_service.generate_response(
                user_message=prompt,
                max_tokens=400
            )
            
            return {
                "content": qwen_response.content,
                "message_type": MessageType.TEXT,
                "metadata": {
                    "analysis_type": "related_news",
                    "related_count": len(related_results)
                }
            }
            
        except Exception as e:
            logger.error(f"查找相关新闻失败: {e}")
            return {
                "content": "抱歉，暂时无法查找相关新闻。请稍后再试或换个问题。"
            }
    
    async def _generate_general_response(
        self,
        user_message: str,
        context: NewsConversationContext,
        conversation_history: List[ChatMessage]
    ) -> Dict[str, Any]:
        """生成通用回复"""
        
        # 构建对话历史
        history_text = "\n".join([
            f"{msg.role}: {msg.content[:100]}..." 
            for msg in conversation_history[-5:]
        ])
        
        current_news_info = ""
        if context.current_news and context.news_cards:
            latest_card = context.news_cards[-1]
            current_news_info = f"""
当前讨论的新闻: {latest_card.title}
核心主题: {', '.join(latest_card.metadata.themes)}
"""
        
        prompt = f"""
作为新闻分析助手，回应用户的问题:

用户问题: {user_message}

对话历史:
{history_text}

{current_news_info}

请提供有帮助的回复，保持：
1. 专业但友好的语调
2. 结合新闻分析的专业知识
3. 适当引导深度讨论
4. 150-250字

如果用户问题与新闻无关，请礼貌地引导回新闻讨论。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=400
        )
        
        return {
            "content": qwen_response.content,
            "message_type": MessageType.TEXT,
            "metadata": {"analysis_type": "general"}
        }
    
    async def _generate_contextual_questions(
        self,
        news_card: NewsCard,
        user_message: str,
        context: NewsConversationContext
    ) -> List[str]:
        """生成上下文相关的建议问题"""
        
        prompt = f"""
基于当前对话生成新的建议问题:

新闻: {news_card.title}
用户刚才问: {user_message}
对话轮次: {len(context.news_cards)}

生成3个深度递进的问题，应该:
1. 比用户刚才的问题更深入
2. 探索不同维度
3. 激发进一步思考

直接返回3个问题，每行一个。
"""
        
        qwen_response = await self.qwen_service.generate_response(
            user_message=prompt,
            max_tokens=150
        )
        
        questions = [q.strip() for q in qwen_response.content.split('\n') if q.strip()]
        return questions[:3]
    
    def _get_recent_messages(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """获取最近的消息"""
        if session_id not in self._messages:
            return []
        return self._messages[session_id][-limit:]
    
    def _get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """获取对话上下文摘要"""
        if session_id not in self._contexts:
            return {}
        
        context = self._contexts[session_id]
        return {
            "analyzed_news_count": len(context.news_cards),
            "current_news_title": context.current_news.title if context.current_news else None,
            "conversation_theme": context.conversation_theme,
            "user_interests": context.user_interests
        }
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        if session_id not in self._sessions:
            return {"error": "会话不存在"}
        
        # 安全地序列化包含datetime的对象
        session_data = self._sessions[session_id].model_dump()
        messages_data = [msg.model_dump() for msg in self._messages.get(session_id, [])]
        
        return {
            "session": session_data,
            "messages": messages_data,
            "context": self._get_context_summary(session_id)
        } 