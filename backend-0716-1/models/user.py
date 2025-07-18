"""
用户相关数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserSessionRequest(BaseModel):
    """用户会话创建请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_name: Optional[str] = Field(None, description="会话名称，默认为会话ID")


class UserCreateResult(BaseModel):
    """用户创建结果模型"""
    user_id: str
    username: str


class UserLoginResult(BaseModel):
    """用户登录结果模型"""
    user_id: str
    username: str
    sessions: List[Dict[str, Any]] = []


class UserSessionResult(BaseModel):
    """用户会话操作结果模型"""
    session_id: str
    session_name: str


class UserDeleteRequest(BaseModel):
    """用户删除请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class SessionDeleteResponse(BaseModel):
    """会话删除响应模型"""
    status: str
    message: str
    deleted_news: int = 0


class UserDeleteResponse(BaseModel):
    """用户删除响应模型"""
    status: str
    message: str
    deleted_sessions: int = 0
    deleted_news: int = 0


class UserSessionsResponse(BaseModel):
    """用户会话列表响应模型"""
    user_id: str
    sessions: List[Dict[str, Any]] = []
    session_count: int = 0
    status: str = "success"
