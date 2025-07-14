"""
聊天对话数据模型
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    NEWS_CARD = "news_card"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class ChatStatus(str, Enum):
    """对话状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: Optional[str] = Field(None, description="消息ID")
    session_id: str = Field(..., description="会话ID")
    
    # 消息内容
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    # 新闻相关（如果消息类型是新闻卡片）
    news_ids: List[str] = Field(default_factory=list, description="关联的新闻ID列表")
    
    # AI 生成相关
    llm_model: Optional[str] = Field(None, description="使用的模型名称")
    tokens_used: Optional[int] = Field(None, description="使用的令牌数")
    generation_time: Optional[float] = Field(None, description="生成时间（秒）")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """聊天会话模型"""
    id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID（匿名用户为空）")
    
    # 会话信息
    title: str = Field(default="新对话", description="会话标题", max_length=200)
    summary: Optional[str] = Field(None, description="会话摘要", max_length=1000)
    
    # 状态和设置
    status: ChatStatus = Field(default=ChatStatus.ACTIVE, description="会话状态")
    is_pinned: bool = Field(default=False, description="是否置顶")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    
    # 统计信息
    message_count: int = Field(default=0, description="消息数量")
    total_tokens: int = Field(default=0, description="总令牌数")
    
    # 设置
    settings: Dict[str, Any] = Field(default_factory=dict, description="模型设置")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="会话元数据")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatMessageCreate(BaseModel):
    """创建聊天消息模型"""
    session_id: Optional[str] = Field(None, description="会话ID（新会话时为空）")
    content: str = Field(..., description="消息内容", max_length=4000)
    message_type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    
    # 查询相关设置
    include_news: bool = Field(default=True, description="是否包含新闻搜索")
    news_limit: int = Field(default=5, ge=1, le=20, description="新闻搜索限制")
    
    # 模型设置
    llm_model: Optional[str] = Field(None, description="指定使用的模型")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="最大令牌数")


class ChatSessionCreate(BaseModel):
    """创建聊天会话模型"""
    title: Optional[str] = Field(None, description="会话标题", max_length=200)
    settings: Dict[str, Any] = Field(default_factory=dict, description="模型设置")


class ChatSessionUpdate(BaseModel):
    """更新聊天会话模型"""
    title: Optional[str] = Field(None, description="会话标题", max_length=200)
    is_pinned: Optional[bool] = Field(None, description="是否置顶")
    status: Optional[ChatStatus] = Field(None, description="会话状态")
    settings: Optional[Dict[str, Any]] = Field(None, description="模型设置")

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """聊天响应模型"""
    session: ChatSession = Field(..., description="会话信息")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    
    # 响应统计
    response_time: float = Field(..., description="响应时间（秒）")
    tokens_used: int = Field(default=0, description="本次使用的令牌数")

    class Config:
        from_attributes = True


class ChatHistory(BaseModel):
    """聊天历史模型"""
    sessions: List[ChatSession] = Field(..., description="会话列表")
    total: int = Field(..., description="总会话数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页面大小")

    class Config:
        from_attributes = True


class MessageReaction(BaseModel):
    """消息反应模型"""
    message_id: str = Field(..., description="消息ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    reaction_type: str = Field(..., description="反应类型（like, dislike, helpful, etc.）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 