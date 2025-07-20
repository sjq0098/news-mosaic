"""
用户记忆和个性化数据模型 - 支持增强对话服务
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class InterestCategory(str, Enum):
    """兴趣分类枚举"""
    TECHNOLOGY = "technology"        # 科技
    FINANCE = "finance"             # 财经
    POLITICS = "politics"           # 政治
    SPORTS = "sports"               # 体育
    ENTERTAINMENT = "entertainment" # 娱乐
    HEALTH = "health"               # 健康
    EDUCATION = "education"         # 教育
    LIFESTYLE = "lifestyle"         # 生活
    SCIENCE = "science"             # 科学
    BUSINESS = "business"           # 商业
    INTERNATIONAL = "international" # 国际
    LOCAL = "local"                 # 本地


class MemoryType(str, Enum):
    """记忆类型枚举"""
    PREFERENCE = "preference"       # 偏好记忆
    FACT = "fact"                  # 事实记忆
    CONTEXT = "context"            # 上下文记忆
    INTERACTION = "interaction"     # 交互记忆


class UserPreference(BaseModel):
    """用户偏好模型"""
    # 内容偏好
    preferred_categories: List[InterestCategory] = Field(default_factory=list, description="偏好的新闻分类")
    disliked_categories: List[InterestCategory] = Field(default_factory=list, description="不喜欢的新闻分类")
    
    # 新闻偏好
    preferred_news_length: str = Field(default="medium", description="偏好的新闻长度：short/medium/long")
    preferred_analysis_depth: str = Field(default="detailed", description="偏好的分析深度：brief/detailed/comprehensive")
    
    # 对话偏好
    communication_style: str = Field(default="professional", description="沟通风格：casual/professional/academic")
    response_format: str = Field(default="structured", description="回复格式：simple/structured/detailed")
    
    # 语言和地区偏好
    preferred_language: str = Field(default="zh-CN", description="偏好语言")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="偏好更新时间")


class MemoryItem(BaseModel):
    """记忆项模型"""
    id: Optional[str] = Field(None, description="记忆ID")
    user_id: str = Field(..., description="用户ID")
    
    # 记忆内容
    memory_type: MemoryType = Field(..., description="记忆类型")
    content: str = Field(..., description="记忆内容")
    context: Dict[str, Any] = Field(default_factory=dict, description="记忆上下文")
    
    # 重要性和置信度
    importance_score: float = Field(default=0.5, description="重要性分数", ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.8, description="置信度分数", ge=0.0, le=1.0)
    
    # 关联信息
    related_topics: List[str] = Field(default_factory=list, description="相关话题")
    related_news_ids: List[str] = Field(default_factory=list, description="相关新闻ID")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow, description="最后访问时间")
    access_count: int = Field(default=1, description="访问次数")
    
    # 有效性
    is_active: bool = Field(default=True, description="是否有效")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ConversationContext(BaseModel):
    """对话上下文模型"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    
    # 当前对话状态
    current_topic: Optional[str] = Field(None, description="当前话题")
    discussed_topics: List[str] = Field(default_factory=list, description="已讨论话题")
    
    # 上下文信息
    referenced_news: List[str] = Field(default_factory=list, description="引用的新闻ID")
    mentioned_entities: List[str] = Field(default_factory=list, description="提及的实体")
    user_questions: List[str] = Field(default_factory=list, description="用户问题历史")
    
    # 对话特征
    conversation_sentiment: str = Field(default="neutral", description="对话情感倾向")
    complexity_level: str = Field(default="medium", description="对话复杂度")
    
    # 时间信息
    started_at: datetime = Field(default_factory=datetime.utcnow, description="开始时间")
    last_updated_at: datetime = Field(default_factory=datetime.utcnow, description="最后更新时间")
    message_count: int = Field(default=0, description="消息数量")


class UserMemoryProfile(BaseModel):
    """用户记忆档案"""
    user_id: str = Field(..., description="用户ID")
    
    # 偏好信息
    preferences: UserPreference = Field(default_factory=UserPreference, description="用户偏好")
    
    # 记忆集合
    memories: List[MemoryItem] = Field(default_factory=list, description="用户记忆集合")
    
    # 统计信息
    total_conversations: int = Field(default=0, description="总对话数")
    total_memories: int = Field(default=0, description="总记忆数")
    memory_retention_days: int = Field(default=30, description="记忆保留天数")
    
    # 个性化得分
    personalization_score: float = Field(default=0.0, description="个性化程度得分", ge=0.0, le=1.0)
    interaction_frequency: float = Field(default=0.0, description="交互频率", ge=0.0, le=1.0)
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class MemoryQueryRequest(BaseModel):
    """记忆查询请求"""
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="查询内容")
    
    # 查询参数
    memory_types: Optional[List[MemoryType]] = Field(None, description="记忆类型过滤")
    categories: Optional[List[InterestCategory]] = Field(None, description="分类过滤")
    importance_threshold: float = Field(default=0.3, description="重要性阈值", ge=0.0, le=1.0)
    max_results: int = Field(default=10, description="最大结果数", ge=1, le=50)
    
    # 时间过滤
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")


class MemoryQueryResponse(BaseModel):
    """记忆查询响应"""
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="查询内容")
    
    # 查询结果
    memories: List[MemoryItem] = Field(..., description="匹配的记忆")
    total_count: int = Field(..., description="总匹配数")
    
    # 相关性信息
    relevance_scores: List[float] = Field(..., description="相关性分数")
    context_summary: str = Field(..., description="上下文摘要")
    
    # 查询统计
    query_time_ms: float = Field(..., description="查询耗时（毫秒）")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="处理时间") 