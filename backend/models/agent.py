"""
智能体模型定义
"""

from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field
from models.user import UserPreferences


class AgentState(TypedDict):
    """智能体状态定义，消息自动合并，字段清晰对应工作流逻辑"""
    messages: List  # 使用 langgraph 消息合并机制，动态合并新消息
    user_id: str
    session_id: str
    user_preferences: Optional[UserPreferences]  # 用户偏好数据
    extracted_keywords: List[str]  # 关键词抽取结果
    extracted_time_period: Optional[str]  # 提取的时间范围
    search_result: Optional[Dict[str, Any]]  # 搜索结果
    response_type: str  # 响应类型
    interest_operation: Optional[str]  # 兴趣操作类型
    interests_to_manage: List[str]  # 待管理兴趣关键词列表


class AgentResponse(BaseModel):
    """智能体响应模型"""
    reply: str = Field(..., description="智能体回复内容")
    type: str = Field(..., description="响应类型")
    keywords_used: List[str] = Field(default_factory=list, description="使用的关键词")
    search_result: Optional[Dict[str, Any]] = Field(None, description="搜索结果")
    model_used: Optional[str] = Field(None, description="使用的AI模型")
    error: Optional[str] = Field(None, description="错误信息")


class ChatMessage(BaseModel):
    """聊天消息模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="消息内容")
    model_name: Optional[str] = Field(None, description="指定使用的AI模型名称")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[AgentResponse] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")