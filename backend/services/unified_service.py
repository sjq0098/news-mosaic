"""
统一服务层 - 集成增强对话、RAG检索和新闻卡片生成的完整解决方案
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from pydantic import BaseModel, Field

from services.enhanced_chat_service import (
    EnhancedChatService, EnhancedChatRequest, EnhancedChatResponse,
    enhanced_chat_service
)
from services.integrated_rag_service import IntegratedRAGService
from services.conversation_context_manager import context_manager
from models.news_card import NewsCardResponse
from models.chat import MessageType


class UnifiedServiceRequest(BaseModel):
    """统一服务请求"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="用户查询")
    
    # 服务选项
    enable_enhanced_chat: bool = Field(default=True, description="启用增强对话")
    enable_news_card: bool = Field(default=False, description="启用新闻卡片生成")
    enable_memory: bool = Field(default=True, description="启用用户记忆")
    enable_rag: bool = Field(default=True, description="启用RAG检索")
    
    # 个性化选项
    response_style: Optional[str] = Field(None, description="回复风格")
    card_generation_priority: str = Field(default="quality", description="卡片生成优先级")
    
    # 高级选项
    max_news_results: int = Field(default=3, description="最大新闻检索数", ge=1, le=10)
    context_depth: str = Field(default="medium", description="上下文深度")


class UnifiedServiceResponse(BaseModel):
    """统一服务响应"""
    request_id: str = Field(..., description="请求ID")
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    
    # 主要响应内容
    ai_response: str = Field(..., description="AI智能回复")
    response_type: MessageType = Field(default=MessageType.TEXT, description="回复类型")
    
    # 可选的新闻卡片
    news_card: Optional[Any] = Field(None, description="生成的新闻卡片")
    
    # 上下文和个性化信息
    personalization_applied: bool = Field(default=False, description="是否应用了个性化")
    context_summary: str = Field(..., description="上下文摘要")
    used_features: List[str] = Field(..., description="使用的功能列表")
    
    # 相关信息
    related_news: List[Dict[str, Any]] = Field(default_factory=list, description="相关新闻")
    suggested_topics: List[str] = Field(default_factory=list, description="推荐话题")
    memory_insights: List[str] = Field(default_factory=list, description="记忆洞察")
    
    # 性能指标
    total_processing_time_ms: float = Field(..., description="总处理时间（毫秒）")
    feature_timings: Dict[str, float] = Field(..., description="各功能耗时")
    confidence_score: float = Field(default=0.8, description="整体置信度")
    
    # 质量指标
    response_quality_score: float = Field(default=0.8, description="回复质量分数")
    context_relevance_score: float = Field(default=0.8, description="上下文相关性分数")


class UnifiedService:
    """统一服务 - 集成所有RAG和对话功能"""
    
    def __init__(self):
        self.enhanced_chat_service = enhanced_chat_service
        self.rag_service = IntegratedRAGService()
        self.context_manager = context_manager
        
        # 性能监控
        self.request_count = 0
        self.total_processing_time = 0.0
        
        logger.info("统一服务已初始化")
    
    async def initialize(self):
        """初始化所有服务组件"""
        try:
            logger.info("🚀 开始初始化统一服务...")
            
            # 初始化增强对话服务
            await self.enhanced_chat_service.initialize()
            
            # 初始化RAG服务
            await self.rag_service.initialize_pipeline()
            
            logger.info("✅ 统一服务初始化完成")
            
        except Exception as e:
            logger.error(f"统一服务初始化失败: {e}")
            raise
    
    async def process_unified_request(
        self, 
        request: UnifiedServiceRequest
    ) -> UnifiedServiceResponse:
        """处理统一服务请求"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        feature_timings = {}
        used_features = []
        
        try:
            logger.info(f"🎯 处理统一请求 {request_id}: {request.query[:50]}...")
            
            # 1. 增强对话处理 (核心功能)
            ai_response = ""
            personalization_applied = False
            context_summary = ""
            suggested_topics = []
            memory_insights = []
            
            if request.enable_enhanced_chat:
                chat_start = time.time()
                
                chat_request = EnhancedChatRequest(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message=request.query,
                    include_memory=request.enable_memory,
                    include_rag=request.enable_rag,
                    include_news_card=False,  # 新闻卡片单独处理
                    response_style=request.response_style,
                    max_context_memories=self._get_max_memories_by_depth(request.context_depth)
                )
                
                chat_response = await self.enhanced_chat_service.chat_with_enhanced_context(chat_request)
                
                ai_response = chat_response.response
                personalization_applied = chat_response.personalization_applied
                context_summary = chat_response.context_summary
                suggested_topics = chat_response.suggested_topics
                
                feature_timings["enhanced_chat"] = (time.time() - chat_start) * 1000
                used_features.append("增强对话")
                
                # 提取记忆洞察
                if chat_response.used_memories_count > 0:
                    memory_insights.append(f"使用了 {chat_response.used_memories_count} 条历史记忆")
                    used_features.append("用户记忆")
            
            # 2. 新闻卡片生成 (可选)
            news_card = None
            if request.enable_news_card:
                card_start = time.time()
                
                try:
                    # 使用完整的RAG增强卡片生成
                    news_card = await self.rag_service.generate_news_card(request.query)
                    
                    if news_card:
                        used_features.append("新闻卡片生成")
                    
                except Exception as e:
                    logger.warning(f"新闻卡片生成失败: {e}")
                
                feature_timings["news_card"] = (time.time() - card_start) * 1000
            
            # 3. 相关新闻检索 (增强信息)
            related_news = []
            if request.enable_rag:
                rag_start = time.time()
                
                try:
                    raw_news = await self.rag_service.search_relevant_news(
                        query=request.query, 
                        top_k=request.max_news_results
                    )
                    
                    related_news = [
                        {
                            "title": news.get("title", ""),
                            "source": news.get("source", ""),
                            "category": news.get("category", ""),
                            "similarity": round(news.get("similarity", 0.0), 3),
                            "summary": news.get("content", "")[:150] + "..." if news.get("content") else ""
                        }
                        for news in raw_news
                    ]
                    
                    if related_news:
                        used_features.append("RAG新闻检索")
                    
                except Exception as e:
                    logger.warning(f"相关新闻检索失败: {e}")
                
                feature_timings["rag_search"] = (time.time() - rag_start) * 1000
            
            # 4. 后处理和质量评估
            post_start = time.time()
            
            # 计算质量分数
            response_quality_score = self._calculate_response_quality(
                response=ai_response,
                has_news_context=len(related_news) > 0,
                personalized=personalization_applied,
                memory_used=request.enable_memory
            )
            
            # 计算上下文相关性
            context_relevance_score = self._calculate_context_relevance(
                query=request.query,
                response=ai_response,
                related_news=related_news
            )
            
            # 更新上下文摘要
            if not context_summary:
                context_summary = self._generate_unified_context_summary(
                    used_features=used_features,
                    news_count=len(related_news),
                    personalized=personalization_applied
                )
            
            feature_timings["post_processing"] = (time.time() - post_start) * 1000
            
            # 5. 构建统一响应
            total_time = (time.time() - start_time) * 1000
            
            response = UnifiedServiceResponse(
                request_id=request_id,
                user_id=request.user_id,
                session_id=request.session_id,
                ai_response=ai_response,
                news_card=news_card,
                personalization_applied=personalization_applied,
                context_summary=context_summary,
                used_features=used_features,
                related_news=related_news,
                suggested_topics=suggested_topics,
                memory_insights=memory_insights,
                total_processing_time_ms=total_time,
                feature_timings=feature_timings,
                response_quality_score=response_quality_score,
                context_relevance_score=context_relevance_score
            )
            
            # 更新统计信息
            self.request_count += 1
            self.total_processing_time += total_time
            
            logger.info(f"✅ 统一请求处理完成 {request_id}, 耗时: {total_time:.2f}ms, 功能: {', '.join(used_features)}")
            
            return response
            
        except Exception as e:
            logger.error(f"统一请求处理失败 {request_id}: {e}")
            raise
    
    def _get_max_memories_by_depth(self, depth: str) -> int:
        """根据上下文深度获取最大记忆数"""
        depth_mapping = {
            "shallow": 2,
            "medium": 5,
            "deep": 10
        }
        return depth_mapping.get(depth, 5)
    
    def _calculate_response_quality(
        self, 
        response: str, 
        has_news_context: bool, 
        personalized: bool, 
        memory_used: bool
    ) -> float:
        """计算回复质量分数"""
        base_score = 0.6
        
        # 长度质量
        if len(response) > 100:
            base_score += 0.1
        if len(response) > 300:
            base_score += 0.1
        
        # 上下文丰富度
        if has_news_context:
            base_score += 0.1
        
        # 个性化程度
        if personalized:
            base_score += 0.1
        
        # 记忆使用
        if memory_used:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_context_relevance(
        self, 
        query: str, 
        response: str, 
        related_news: List[Dict]
    ) -> float:
        """计算上下文相关性分数"""
        base_score = 0.5
        
        # 查询关键词在回复中的出现
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        keyword_overlap = len(query_words & response_words) / max(len(query_words), 1)
        base_score += keyword_overlap * 0.3
        
        # 新闻相关性
        if related_news:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _generate_unified_context_summary(
        self, 
        used_features: List[str], 
        news_count: int, 
        personalized: bool
    ) -> str:
        """生成统一的上下文摘要"""
        summary_parts = []
        
        if used_features:
            summary_parts.append(f"使用功能: {', '.join(used_features)}")
        
        if news_count > 0:
            summary_parts.append(f"检索到 {news_count} 条相关新闻")
        
        if personalized:
            summary_parts.append("应用个性化配置")
        
        return "; ".join(summary_parts) if summary_parts else "基础处理模式"
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        avg_processing_time = (
            self.total_processing_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "service_name": "统一RAG服务",
            "status": "active",
            "request_count": self.request_count,
            "average_processing_time_ms": round(avg_processing_time, 2),
            "features": [
                "增强对话",
                "RAG检索", 
                "新闻卡片生成",
                "用户记忆",
                "个性化回复"
            ],
            "initialized_at": datetime.utcnow().isoformat()
        }
    
    async def clear_user_data(self, user_id: str):
        """清理用户数据"""
        try:
            # 清理用户记忆
            if user_id in self.context_manager.user_profiles:
                del self.context_manager.user_profiles[user_id]
            
            # 清理对话历史
            sessions_to_clear = []
            for session_id, messages in self.enhanced_chat_service.conversation_history.items():
                if messages and messages[0].metadata.get("user_id") == user_id:
                    sessions_to_clear.append(session_id)
            
            for session_id in sessions_to_clear:
                await self.enhanced_chat_service.clear_conversation_history(session_id)
            
            logger.info(f"已清理用户 {user_id} 的所有数据")
            
        except Exception as e:
            logger.error(f"清理用户数据失败: {e}")


# 创建全局实例
unified_service = UnifiedService() 