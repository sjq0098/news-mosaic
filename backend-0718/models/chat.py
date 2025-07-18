"""
对话相关的数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChatMessageType(str, Enum):
    """消息类型枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: Optional[str] = Field(None, description="消息ID")
    type: ChatMessageType = Field(..., description="消息类型")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="请求时间")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message_id: str = Field(..., description="消息ID")
    reply: str = Field(..., description="回复内容")
    reply_type: str = Field(..., description="回复类型")
    keywords_extracted: List[str] = Field(default_factory=list, description="提取的关键词")
    news_found: int = Field(0, description="找到的新闻数量")
    success: bool = Field(True, description="是否成功")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ChatSession(BaseModel):
    """聊天会话模型"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="会话标题")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    message_count: int = Field(0, description="消息数量")
    is_active: bool = Field(True, description="是否活跃")


class ChatHistory(BaseModel):
    """聊天历史模型"""
    session_id: str = Field(..., description="会话ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息列表")
    total_count: int = Field(0, description="总消息数")
    page: int = Field(1, description="页码")
    page_size: int = Field(20, description="每页大小")


class ChatHistoryItem(BaseModel):
    """聊天历史项模型"""
    timestamp: str = Field(..., description="时间戳")
    user: str = Field(..., description="用户消息")
    assistant: str = Field(..., description="助手回复")


class SessionMemory(BaseModel):
    """会话记忆模型"""
    session_id: str = Field(..., description="会话ID")
    conversation_history: List[ChatHistoryItem] = Field(default_factory=list, description="对话历史")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class ChatMemoryDocument(BaseModel):
    """聊天记忆文档模型"""
    id: str = Field(..., alias="_id", description="记忆ID（通常与session_id相同）")
    session_id: str = Field(..., description="会话ID")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    model_config = {"populate_by_name": True}
