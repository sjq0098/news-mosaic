"""
对话上下文管理器 - 维护多轮对话状态和用户记忆
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

from models.user_memory import (
    UserMemoryProfile, MemoryItem, ConversationContext, 
    UserPreference, MemoryType, InterestCategory,
    MemoryQueryRequest, MemoryQueryResponse
)
from models.chat import ChatMessage, MessageRole
from services.embedding_service import QWenEmbeddingService


class ConversationContextManager:
    """对话上下文管理器"""
    
    def __init__(self):
        self.embedding_service = QWenEmbeddingService()
        
        # 内存存储 (生产环境中应使用数据库)
        self.user_profiles: Dict[str, UserMemoryProfile] = {}
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.memory_embeddings: Dict[str, List[float]] = {}
        
        logger.info("对话上下文管理器已初始化")
    
    async def get_or_create_user_profile(self, user_id: str) -> UserMemoryProfile:
        """获取或创建用户记忆档案"""
        if user_id not in self.user_profiles:
            profile = UserMemoryProfile(user_id=user_id)
            self.user_profiles[user_id] = profile
            logger.info(f"为用户 {user_id} 创建新的记忆档案")
        
        return self.user_profiles[user_id]
    
    async def get_or_create_conversation_context(
        self, 
        session_id: str, 
        user_id: str
    ) -> ConversationContext:
        """获取或创建对话上下文"""
        if session_id not in self.active_contexts:
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id
            )
            self.active_contexts[session_id] = context
            logger.info(f"为会话 {session_id} 创建新的对话上下文")
        
        return self.active_contexts[session_id]
    
    async def add_memory(
        self, 
        user_id: str, 
        content: str, 
        memory_type: MemoryType,
        context: Dict[str, Any] = None,
        importance_score: float = 0.5,
        related_topics: List[str] = None
    ) -> MemoryItem:
        """添加用户记忆"""
        try:
            profile = await self.get_or_create_user_profile(user_id)
            
            # 创建记忆项
            memory = MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                context=context or {},
                importance_score=importance_score,
                related_topics=related_topics or []
            )
            
            # 生成embedding
            embedding = await self.embedding_service.get_embeddings([content])
            if embedding:
                self.memory_embeddings[memory.id] = embedding[0]
            
            # 添加到用户档案
            profile.memories.append(memory)
            profile.total_memories = len(profile.memories)
            profile.updated_at = datetime.utcnow()
            
            logger.info(f"为用户 {user_id} 添加 {memory_type.value} 类型记忆")
            return memory
            
        except Exception as e:
            logger.error(f"添加用户记忆失败: {e}")
            raise
    
    async def query_memories(
        self, 
        request: MemoryQueryRequest
    ) -> MemoryQueryResponse:
        """查询用户记忆"""
        start_time = datetime.utcnow()
        
        try:
            profile = await self.get_or_create_user_profile(request.user_id)
            
            # 生成查询embedding
            query_embedding = await self.embedding_service.get_embeddings([request.query])
            if not query_embedding:
                return MemoryQueryResponse(
                    user_id=request.user_id,
                    query=request.query,
                    memories=[],
                    total_count=0,
                    relevance_scores=[],
                    context_summary="无法生成查询向量",
                    query_time_ms=0
                )
            
            # 筛选记忆
            filtered_memories = []
            relevance_scores = []
            
            for memory in profile.memories:
                # 类型过滤
                if request.memory_types and memory.memory_type not in request.memory_types:
                    continue
                
                # 重要性过滤
                if memory.importance_score < request.importance_threshold:
                    continue
                
                # 时间过滤
                if request.start_date and memory.created_at < request.start_date:
                    continue
                if request.end_date and memory.created_at > request.end_date:
                    continue
                
                # 活跃状态过滤
                if not memory.is_active:
                    continue
                
                # 计算相关性
                if memory.id in self.memory_embeddings:
                    similarity = self._calculate_similarity(
                        query_embedding[0], 
                        self.memory_embeddings[memory.id]
                    )
                    
                    if similarity > 0.3:  # 相关性阈值
                        filtered_memories.append(memory)
                        relevance_scores.append(similarity)
            
            # 按相关性排序
            if filtered_memories:
                sorted_pairs = sorted(
                    zip(filtered_memories, relevance_scores),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                filtered_memories = [pair[0] for pair in sorted_pairs[:request.max_results]]
                relevance_scores = [pair[1] for pair in sorted_pairs[:request.max_results]]
            
            # 生成上下文摘要
            context_summary = self._generate_context_summary(filtered_memories)
            
            # 计算查询时间
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return MemoryQueryResponse(
                user_id=request.user_id,
                query=request.query,
                memories=filtered_memories,
                total_count=len(filtered_memories),
                relevance_scores=relevance_scores,
                context_summary=context_summary,
                query_time_ms=query_time
            )
            
        except Exception as e:
            logger.error(f"查询用户记忆失败: {e}")
            raise
    
    async def update_conversation_context(
        self, 
        session_id: str, 
        message: ChatMessage,
        extracted_topics: List[str] = None,
        mentioned_entities: List[str] = None
    ):
        """更新对话上下文"""
        try:
            context = self.active_contexts.get(session_id)
            if not context:
                return
            
            # 更新消息计数
            context.message_count += 1
            context.last_updated_at = datetime.utcnow()
            
            # 更新话题
            if extracted_topics:
                for topic in extracted_topics:
                    if topic not in context.discussed_topics:
                        context.discussed_topics.append(topic)
                
                # 更新当前话题为最新的
                if extracted_topics:
                    context.current_topic = extracted_topics[-1]
            
            # 更新提及的实体
            if mentioned_entities:
                for entity in mentioned_entities:
                    if entity not in context.mentioned_entities:
                        context.mentioned_entities.append(entity)
            
            # 如果是用户消息，记录问题
            if message.role == MessageRole.USER:
                if "?" in message.content or "？" in message.content:
                    context.user_questions.append(message.content)
            
            logger.debug(f"更新会话 {session_id} 的对话上下文")
            
        except Exception as e:
            logger.error(f"更新对话上下文失败: {e}")
    
    async def extract_user_preferences(
        self, 
        user_id: str, 
        conversation_history: List[ChatMessage]
    ) -> UserPreference:
        """从对话历史中提取用户偏好"""
        try:
            profile = await self.get_or_create_user_profile(user_id)
            preferences = profile.preferences
            
            # 分析对话内容，提取偏好信息
            content_analysis = await self._analyze_conversation_content(conversation_history)
            
            # 更新偏好分类
            if content_analysis.get("interested_categories"):
                for category in content_analysis["interested_categories"]:
                    if category not in preferences.preferred_categories:
                        preferences.preferred_categories.append(category)
            
            # 更新沟通风格
            if content_analysis.get("communication_style"):
                preferences.communication_style = content_analysis["communication_style"]
            
            # 更新回复格式偏好
            if content_analysis.get("response_format"):
                preferences.response_format = content_analysis["response_format"]
            
            preferences.updated_at = datetime.utcnow()
            return preferences
            
        except Exception as e:
            logger.error(f"提取用户偏好失败: {e}")
            return profile.preferences if profile else UserPreference()
    
    async def get_relevant_context(
        self, 
        user_id: str, 
        current_query: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """获取相关的上下文信息"""
        try:
            # 查询相关记忆
            memory_request = MemoryQueryRequest(
                user_id=user_id,
                query=current_query,
                max_results=5,
                importance_threshold=0.4
            )
            memory_response = await self.query_memories(memory_request)
            
            # 获取对话上下文
            conversation_context = None
            if session_id:
                conversation_context = self.active_contexts.get(session_id)
            
            # 获取用户偏好
            profile = await self.get_or_create_user_profile(user_id)
            
            return {
                "user_preferences": profile.preferences,
                "relevant_memories": memory_response.memories,
                "conversation_context": conversation_context,
                "context_summary": memory_response.context_summary,
                "personalization_score": profile.personalization_score
            }
            
        except Exception as e:
            logger.error(f"获取相关上下文失败: {e}")
            return {}
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算向量相似度（余弦相似度）"""
        try:
            import numpy as np
            
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1_np, vec2_np)
            norm_vec1 = np.linalg.norm(vec1_np)
            norm_vec2 = np.linalg.norm(vec2_np)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_vec1 * norm_vec2)
            return float(similarity)
            
        except Exception:
            return 0.0
    
    def _generate_context_summary(self, memories: List[MemoryItem]) -> str:
        """生成上下文摘要"""
        if not memories:
            return "暂无相关记忆"
        
        # 统计记忆类型
        type_counts = {}
        important_memories = []
        
        for memory in memories:
            type_counts[memory.memory_type.value] = type_counts.get(memory.memory_type.value, 0) + 1
            if memory.importance_score > 0.7:
                important_memories.append(memory.content[:50])
        
        summary_parts = []
        summary_parts.append(f"找到 {len(memories)} 条相关记忆")
        
        if type_counts:
            type_summary = ", ".join([f"{k}: {v}条" for k, v in type_counts.items()])
            summary_parts.append(f"记忆类型分布: {type_summary}")
        
        if important_memories:
            summary_parts.append(f"重要记忆: {'; '.join(important_memories[:3])}")
        
        return "; ".join(summary_parts)
    
    async def _analyze_conversation_content(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """分析对话内容，提取特征"""
        # 简化的内容分析逻辑，实际项目中可以使用更复杂的NLP技术
        analysis = {
            "interested_categories": [],
            "communication_style": "professional",
            "response_format": "structured"
        }
        
        # 分析消息内容，提取关键词和特征
        user_messages = [msg for msg in messages if msg.role == MessageRole.USER]
        
        # 简单的关键词匹配来推断用户兴趣
        tech_keywords = ["AI", "人工智能", "技术", "科技", "算法", "编程"]
        finance_keywords = ["经济", "财经", "股票", "投资", "金融", "市场"]
        
        content_text = " ".join([msg.content for msg in user_messages])
        
        if any(keyword in content_text for keyword in tech_keywords):
            analysis["interested_categories"].append(InterestCategory.TECHNOLOGY)
        
        if any(keyword in content_text for keyword in finance_keywords):
            analysis["interested_categories"].append(InterestCategory.FINANCE)
        
        # 分析沟通风格
        if len(user_messages) > 0:
            avg_length = sum(len(msg.content) for msg in user_messages) / len(user_messages)
            if avg_length > 100:
                analysis["communication_style"] = "detailed"
            elif avg_length < 30:
                analysis["communication_style"] = "casual"
        
        return analysis
    
    async def cleanup_expired_memories(self, user_id: str):
        """清理过期的记忆"""
        try:
            profile = await self.get_or_create_user_profile(user_id)
            
            now = datetime.utcnow()
            retention_period = timedelta(days=profile.memory_retention_days)
            
            active_memories = []
            cleaned_count = 0
            
            for memory in profile.memories:
                # 检查是否过期
                if memory.expires_at and memory.expires_at < now:
                    cleaned_count += 1
                    continue
                
                # 检查是否超过保留期限
                if memory.created_at < (now - retention_period):
                    cleaned_count += 1
                    continue
                
                active_memories.append(memory)
            
            if cleaned_count > 0:
                profile.memories = active_memories
                profile.total_memories = len(active_memories)
                profile.updated_at = now
                
                logger.info(f"为用户 {user_id} 清理了 {cleaned_count} 条过期记忆")
            
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")


# 创建全局实例
context_manager = ConversationContextManager() 