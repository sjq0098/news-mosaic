"""
完整Pipeline服务 - 整合增强对话、RAG、Embedding和卡片生成

此服务作为统一入口，提供完整的新闻智能分析和对话功能
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import asyncio
import logging
from enum import Enum
from pydantic import BaseModel, Field

from .unified_service import UnifiedService, UnifiedServiceRequest, UnifiedServiceResponse
from .enhanced_chat_service import EnhancedChatService, EnhancedChatRequest, EnhancedChatResponse
from .integrated_rag_service import IntegratedRAGService
from .rag_enhanced_card_service import RAGEnhancedCardService
from .embedding_service import QWenEmbeddingService
from .conversation_context_manager import ConversationContextManager
from models.news import NewsModel
from models.chat import ChatMessage, MessageRole
from models.user_memory import UserMemoryProfile, ConversationContext

logger = logging.getLogger(__name__)

class PipelineMode(str, Enum):
    """Pipeline处理模式"""
    ENHANCED_CHAT = "enhanced_chat"  # 仅增强对话
    RAG_ANALYSIS = "rag_analysis"    # 仅RAG分析
    CARD_GENERATION = "card_generation"  # 仅卡片生成
    UNIFIED_COMPLETE = "unified_complete"  # 完整统一处理
    CUSTOM = "custom"  # 自定义组合

class PipelineRequest(BaseModel):
    """Pipeline请求模型"""
    # 基本参数
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    
    # 处理模式
    mode: PipelineMode = Field(default=PipelineMode.UNIFIED_COMPLETE, description="处理模式")
    
    # 功能开关
    enable_memory: bool = Field(default=True, description="启用记忆功能")
    enable_rag: bool = Field(default=True, description="启用RAG检索")
    enable_cards: bool = Field(default=True, description="启用卡片生成")
    enable_personalization: bool = Field(default=True, description="启用个性化")
    
    # RAG参数
    rag_query: Optional[str] = Field(None, description="RAG查询内容（默认使用message）")
    max_results: int = Field(default=5, description="最大检索结果数")
    similarity_threshold: float = Field(default=0.7, description="相似度阈值")
    
    # 卡片生成参数
    card_count: int = Field(default=3, description="生成卡片数量")
    card_types: List[str] = Field(default=["summary", "analysis", "impact"], description="卡片类型")
    
    # 个性化参数
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")
    context_window: int = Field(default=10, description="上下文窗口大小")

class PipelineFeatureResult(BaseModel):
    """Pipeline功能结果"""
    enabled: bool
    success: bool
    execution_time: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PipelineResponse(BaseModel):
    """Pipeline响应模型"""
    # 基本信息
    user_id: str
    session_id: str
    timestamp: datetime
    mode: PipelineMode
    
    # 处理结果
    success: bool
    total_execution_time: float
    
    # 主要响应
    ai_response: str
    confidence_score: float
    
    # 功能结果
    enhanced_chat: PipelineFeatureResult
    rag_analysis: PipelineFeatureResult
    card_generation: PipelineFeatureResult
    memory_management: PipelineFeatureResult
    
    # 详细数据
    retrieved_news: List[Dict[str, Any]] = Field(default_factory=list)
    generated_cards: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_context: Optional[Dict[str, Any]] = None
    user_memory_updates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 建议和推荐
    suggested_questions: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    
    # 性能指标
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    quality_scores: Dict[str, float] = Field(default_factory=dict)

class CompletePipelineService:
    """完整Pipeline服务"""
    
    def __init__(self):
        """初始化服务"""
        self.unified_service = UnifiedService()
        self.enhanced_chat_service = EnhancedChatService()
        self.rag_service = IntegratedRAGService()
        self.card_service = RAGEnhancedCardService()
        self.embedding_service = QWenEmbeddingService()
        self.context_manager = ConversationContextManager()
        
        logger.info("CompletePipelineService initialized")
    
    async def process_pipeline(self, request: PipelineRequest) -> PipelineResponse:
        """处理Pipeline请求"""
        start_time = datetime.now()
        
        try:
            # 根据模式选择处理方式
            if request.mode == PipelineMode.UNIFIED_COMPLETE:
                return await self._process_unified_complete(request, start_time)
            elif request.mode == PipelineMode.ENHANCED_CHAT:
                return await self._process_enhanced_chat_only(request, start_time)
            elif request.mode == PipelineMode.RAG_ANALYSIS:
                return await self._process_rag_only(request, start_time)
            elif request.mode == PipelineMode.CARD_GENERATION:
                return await self._process_cards_only(request, start_time)
            elif request.mode == PipelineMode.CUSTOM:
                return await self._process_custom_mode(request, start_time)
            else:
                raise ValueError(f"不支持的处理模式: {request.mode}")
                
        except Exception as e:
            logger.error(f"Pipeline处理失败: {e}")
            return self._create_error_response(request, start_time, str(e))
    
    async def _process_unified_complete(self, request: PipelineRequest, start_time: datetime) -> PipelineResponse:
        """处理完整统一模式"""
        logger.info(f"开始完整统一处理: user_id={request.user_id}")
        
        # 准备统一服务请求
        unified_request = UnifiedServiceRequest(
            user_id=request.user_id,
            session_id=request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            query=request.message,  # 修正字段名
            enable_enhanced_chat=True,
            enable_rag=request.enable_rag,
            enable_news_card=request.enable_cards,
            enable_memory=request.enable_memory,
            max_news_results=request.max_results
        )
        
        # 执行统一服务
        unified_response = await self.unified_service.process_unified_request(unified_request)
        
        # 转换为Pipeline响应
        total_time = (datetime.now() - start_time).total_seconds()
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=unified_response.session_id,
            timestamp=start_time,
            mode=request.mode,
            success=unified_response.success,
            total_execution_time=total_time,
            ai_response=unified_response.ai_response,
            confidence_score=unified_response.quality_scores.get("overall", 0.0),
            enhanced_chat=PipelineFeatureResult(
                enabled=True,
                success=unified_response.success,
                execution_time=unified_response.performance_metrics.get("enhanced_chat_time", 0.0),
                result={"response": unified_response.ai_response, "personalized": True}
            ),
            rag_analysis=PipelineFeatureResult(
                enabled=request.enable_rag,
                success=len(unified_response.retrieved_news) > 0,
                execution_time=unified_response.performance_metrics.get("rag_time", 0.0),
                result={"news_count": len(unified_response.retrieved_news)}
            ),
            card_generation=PipelineFeatureResult(
                enabled=request.enable_cards,
                success=len(unified_response.generated_cards) > 0,
                execution_time=unified_response.performance_metrics.get("card_generation_time", 0.0),
                result={"cards_count": len(unified_response.generated_cards)}
            ),
            memory_management=PipelineFeatureResult(
                enabled=request.enable_memory,
                success=len(unified_response.memory_insights) > 0,
                execution_time=unified_response.feature_timings.get("memory_time", 0.0),
                result={"memories_stored": len(unified_response.memory_insights)}
            ),
            retrieved_news=unified_response.related_news,
            generated_cards=[unified_response.news_card] if unified_response.news_card else [],
            conversation_context={"context_summary": unified_response.context_summary},
            user_memory_updates=unified_response.memory_insights,
            suggested_questions=self._extract_suggested_questions(unified_response),
            related_topics=self._extract_related_topics(unified_response),
            performance_metrics=unified_response.feature_timings,
            quality_scores={"overall": unified_response.confidence_score, "context_relevance": unified_response.context_relevance_score}
        )
    
    async def _process_enhanced_chat_only(self, request: PipelineRequest, start_time: datetime) -> PipelineResponse:
        """仅处理增强对话"""
        logger.info(f"开始增强对话处理: user_id={request.user_id}")
        
        chat_start = datetime.now()
        
        # 准备增强对话请求
        chat_request = EnhancedChatRequest(
            user_id=request.user_id,
            session_id=request.session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            message=request.message,
            enable_memory=request.enable_memory,
            enable_personalization=request.enable_personalization,
            context_window=request.context_window,
            user_preferences=request.user_preferences or {}
        )
        
        # 执行增强对话
        chat_response = await self.enhanced_chat_service.chat_with_enhanced_context(chat_request)
        
        chat_time = (datetime.now() - chat_start).total_seconds()
        total_time = (datetime.now() - start_time).total_seconds()
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=chat_response.session_id,
            timestamp=start_time,
            mode=request.mode,
            success=True,  # 如果到这里说明成功
            total_execution_time=total_time,
            ai_response=chat_response.response,  # 修正字段名
            confidence_score=0.8,  # 临时固定值
            enhanced_chat=PipelineFeatureResult(
                enabled=True,
                success=True,
                execution_time=chat_time,
                result={"personalized": True}  # 临时固定值
            ),
            rag_analysis=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            card_generation=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            memory_management=PipelineFeatureResult(
                enabled=request.enable_memory,
                success=chat_response.used_memories_count > 0,
                execution_time=0.0,
                result={"memories_stored": chat_response.used_memories_count}
            ),
            conversation_context={"context_summary": chat_response.context_summary},
            user_memory_updates=[],  # 暂时为空列表
            suggested_questions=chat_response.suggested_topics[:3] if chat_response.suggested_topics else [],
            performance_metrics={"chat_time": chat_time, "total_time": total_time},
            quality_scores={"confidence": chat_response.confidence_score, "overall": chat_response.confidence_score}
        )
    
    async def _process_rag_only(self, request: PipelineRequest, start_time: datetime) -> PipelineResponse:
        """仅处理RAG分析"""
        logger.info(f"开始RAG分析: query={request.rag_query or request.message}")
        
        rag_start = datetime.now()
        
        # 执行RAG检索和对话
        rag_response = await self.rag_service.chat_with_news_context(
            query=request.rag_query or request.message
        )
        
        rag_time = (datetime.now() - rag_start).total_seconds()
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 检查是否有错误
        if "error" in rag_response:
            ai_response = f"RAG分析过程中出现错误: {rag_response['error']}"
            success = False
            retrieved_news = []
        else:
            ai_response = rag_response.get("ai_response", "无回复")
            success = True
            retrieved_news = rag_response.get("relevant_news", [])
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=request.session_id or f"rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=start_time,
            mode=request.mode,
            success=success,
            total_execution_time=total_time,
            ai_response=ai_response,
            confidence_score=0.8 if success else 0.0,
            enhanced_chat=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            rag_analysis=PipelineFeatureResult(
                enabled=True,
                success=success,
                execution_time=rag_time,
                result={"news_count": len(retrieved_news), "query": request.rag_query or request.message}
            ),
            card_generation=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            memory_management=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            retrieved_news=retrieved_news,
            performance_metrics={"rag_time": rag_time, "total_time": total_time},
            quality_scores={"rag_relevance": 0.8 if success else 0.0}
        )
    
    async def _process_cards_only(self, request: PipelineRequest, start_time: datetime) -> PipelineResponse:
        """仅处理卡片生成"""
        logger.info(f"开始卡片生成: message={request.message}")
        
        card_start = datetime.now()
        
        # 首先进行RAG检索获取新闻数据
        rag_results = await self.rag_service.enhanced_search(
            query=request.message,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        generated_cards = []
        if rag_results:
            # 为每个新闻生成卡片
            for i, news_data in enumerate(rag_results[:request.card_count]):
                try:
                    card_result = await self.card_service.generate_enhanced_card(
                        news_data=news_data,
                        user_query=request.message
                    )
                    if card_result:
                        generated_cards.append(card_result)
                except Exception as e:
                    logger.error(f"卡片生成失败: {e}")
        
        card_time = (datetime.now() - card_start).total_seconds()
        total_time = (datetime.now() - start_time).total_seconds()
        
        ai_response = f"为您生成了{len(generated_cards)}张新闻卡片"
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=request.session_id or f"cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=start_time,
            mode=request.mode,
            success=len(generated_cards) > 0,
            total_execution_time=total_time,
            ai_response=ai_response,
            confidence_score=0.9 if generated_cards else 0.0,
            enhanced_chat=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            rag_analysis=PipelineFeatureResult(
                enabled=True,
                success=len(rag_results) > 0,
                execution_time=card_time * 0.3,  # RAG时间估算
                result={"news_count": len(rag_results)}
            ),
            card_generation=PipelineFeatureResult(
                enabled=True,
                success=len(generated_cards) > 0,
                execution_time=card_time * 0.7,  # 卡片生成时间估算
                result={"cards_count": len(generated_cards), "types": request.card_types}
            ),
            memory_management=PipelineFeatureResult(enabled=False, success=True, execution_time=0.0),
            retrieved_news=rag_results,
            generated_cards=generated_cards,
            performance_metrics={"card_generation_time": card_time, "total_time": total_time},
            quality_scores={"card_quality": 0.9 if generated_cards else 0.0}
        )
    
    async def _process_custom_mode(self, request: PipelineRequest, start_time: datetime) -> PipelineResponse:
        """处理自定义模式"""
        logger.info(f"开始自定义模式处理: user_id={request.user_id}")
        
        # 并行执行启用的功能
        tasks = []
        task_names = []
        
        if request.enable_rag:
            tasks.append(self._execute_rag_task(request))
            task_names.append("rag")
        
        if request.enable_cards and request.enable_rag:  # 卡片依赖RAG结果
            tasks.append(self._execute_cards_task(request))
            task_names.append("cards")
        
        if request.enable_memory or request.enable_personalization:
            tasks.append(self._execute_chat_task(request))
            task_names.append("chat")
        
        # 执行任务
        results = {}
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(task_names, task_results):
                results[name] = result
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 构建响应
        ai_response = "自定义处理完成"
        success = any(not isinstance(r, Exception) for r in results.values())
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=request.session_id or f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=start_time,
            mode=request.mode,
            success=success,
            total_execution_time=total_time,
            ai_response=ai_response,
            confidence_score=0.8 if success else 0.0,
            enhanced_chat=self._create_feature_result_from_custom(results.get("chat"), "chat"),
            rag_analysis=self._create_feature_result_from_custom(results.get("rag"), "rag"),
            card_generation=self._create_feature_result_from_custom(results.get("cards"), "cards"),
            memory_management=PipelineFeatureResult(
                enabled=request.enable_memory,
                success=success,
                execution_time=0.0
            ),
            performance_metrics={"total_time": total_time, "custom_mode": True}
        )
    
    async def _execute_rag_task(self, request: PipelineRequest) -> Dict[str, Any]:
        """执行RAG任务"""
        start_time = datetime.now()
        try:
            results = await self.rag_service.enhanced_search(
                query=request.rag_query or request.message,
                max_results=request.max_results,
                similarity_threshold=request.similarity_threshold
            )
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "execution_time": execution_time,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    async def _execute_cards_task(self, request: PipelineRequest) -> Dict[str, Any]:
        """执行卡片生成任务"""
        start_time = datetime.now()
        try:
            # 先获取RAG结果
            rag_results = await self.rag_service.enhanced_search(
                query=request.message,
                max_results=request.max_results
            )
            
            cards = []
            for news_data in rag_results[:request.card_count]:
                card = await self.card_service.generate_enhanced_card(
                    news_data=news_data,
                    user_query=request.message
                )
                if card:
                    cards.append(card)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "execution_time": execution_time,
                "results": cards,
                "count": len(cards)
            }
        except Exception as e:
            return {
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    async def _execute_chat_task(self, request: PipelineRequest) -> Dict[str, Any]:
        """执行对话任务"""
        start_time = datetime.now()
        try:
            chat_request = EnhancedChatRequest(
                user_id=request.user_id,
                session_id=request.session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                message=request.message,
                enable_memory=request.enable_memory,
                enable_personalization=request.enable_personalization,
                context_window=request.context_window,
                user_preferences=request.user_preferences or {}
            )
            
            response = await self.enhanced_chat_service.process_enhanced_chat(chat_request)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": response.success,
                "execution_time": execution_time,
                "response": response.ai_response,
                "personalized": response.personalized
            }
        except Exception as e:
            return {
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    def _create_feature_result_from_custom(self, result: Any, feature_type: str) -> PipelineFeatureResult:
        """从自定义结果创建功能结果"""
        if result is None:
            return PipelineFeatureResult(enabled=False, success=True, execution_time=0.0)
        
        if isinstance(result, Exception):
            return PipelineFeatureResult(
                enabled=True,
                success=False,
                execution_time=0.0,
                error=str(result)
            )
        
        return PipelineFeatureResult(
            enabled=True,
            success=result.get("success", False),
            execution_time=result.get("execution_time", 0.0),
            result=result
        )
    
    def _extract_suggested_questions(self, unified_response) -> List[str]:
        """从统一响应中提取建议问题"""
        suggested = []
        
        # 使用已有的推荐话题
        suggested.extend(unified_response.suggested_topics)
        
        # 基于相关新闻生成建议
        if unified_response.related_news:
            for news in unified_response.related_news[:2]:
                title = news.get("title", "")
                if title:
                    suggested.append(f"告诉我更多关于{title[:30]}的信息")
        
        # 通用建议问题
        suggested.extend([
            "这个话题还有什么最新发展？",
            "相关的其他新闻有哪些？",
            "这对我们有什么影响？"
        ])
        
        return suggested[:5]  # 限制数量
    
    def _extract_related_topics(self, unified_response) -> List[str]:
        """从统一响应中提取相关话题"""
        topics = []
        
        # 使用已有的推荐话题
        topics.extend(unified_response.suggested_topics)
        
        # 从新闻标签提取
        if unified_response.related_news:
            for news in unified_response.related_news:
                tags = news.get("tags", [])
                if tags:
                topics.extend(tags)
        
        # 去重并限制数量
        unique_topics = list(set(topics))
        return unique_topics[:10]
    
    def _create_error_response(self, request: PipelineRequest, start_time: datetime, error_msg: str) -> PipelineResponse:
        """创建错误响应"""
        total_time = (datetime.now() - start_time).total_seconds()
        
        return PipelineResponse(
            user_id=request.user_id,
            session_id=request.session_id or f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=start_time,
            mode=request.mode,
            success=False,
            total_execution_time=total_time,
            ai_response=f"处理请求时发生错误: {error_msg}",
            confidence_score=0.0,
            enhanced_chat=PipelineFeatureResult(
                enabled=True,
                success=False,
                execution_time=0.0,
                error=error_msg
            ),
            rag_analysis=PipelineFeatureResult(enabled=False, success=False, execution_time=0.0),
            card_generation=PipelineFeatureResult(enabled=False, success=False, execution_time=0.0),
            memory_management=PipelineFeatureResult(enabled=False, success=False, execution_time=0.0),
            performance_metrics={"error_time": total_time},
            quality_scores={"error": 0.0}
        )

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """获取Pipeline状态"""
        return {
            "status": "运行中",
            "services": {
                "unified_service": "就绪",
                "enhanced_chat": "就绪", 
                "rag_service": "就绪",
                "card_service": "就绪",
                "embedding_service": "就绪",
                "context_manager": "就绪"
            },
            "modes": [mode for mode in PipelineMode.__dict__.values() if not mode.startswith('_')],
            "timestamp": datetime.now().isoformat()
        }