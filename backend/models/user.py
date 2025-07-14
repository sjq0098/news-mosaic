"""
用户数据模型
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


class UserModel(BaseModel):
    """用户基础模型"""
    id: Optional[str] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="邮箱地址")
    
    # 个人信息
    nickname: Optional[str] = Field(None, description="昵称", max_length=100)
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介", max_length=500)
    
    # 权限和状态
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    is_verified: bool = Field(default=False, description="是否已验证")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    # 统计信息
    login_count: int = Field(default=0, description="登录次数")
    search_count: int = Field(default=0, description="搜索次数")
    chat_count: int = Field(default=0, description="对话次数")
    
    # 个性化设置
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好设置")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """创建用户模型"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码", min_length=6, max_length=128)
    
    nickname: Optional[str] = Field(None, description="昵称", max_length=100)
    bio: Optional[str] = Field(None, description="个人简介", max_length=500)


class UserUpdate(BaseModel):
    """更新用户模型"""
    nickname: Optional[str] = Field(None, description="昵称", max_length=100)
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介", max_length=500)
    
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """用户响应模型（不包含敏感信息）"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    
    role: UserRole = Field(..., description="用户角色")
    status: UserStatus = Field(..., description="用户状态")
    is_verified: bool = Field(..., description="是否已验证")
    
    created_at: datetime = Field(..., description="创建时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    login_count: int = Field(..., description="登录次数")
    search_count: int = Field(..., description="搜索次数")
    chat_count: int = Field(..., description="对话次数")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserPasswordChange(BaseModel):
    """密码修改模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=128)


class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    # 新闻偏好
    preferred_categories: List[str] = Field(default_factory=list, description="偏好的新闻分类")
    preferred_sources: List[str] = Field(default_factory=list, description="偏好的新闻来源")
    
    # 语言和地区
    language: str = Field(default="zh-CN", description="语言设置")
    timezone: str = Field(default="Asia/Shanghai", description="时区设置")
    
    # 通知设置
    email_notifications: bool = Field(default=True, description="邮件通知")
    push_notifications: bool = Field(default=True, description="推送通知")
    
    # 显示设置
    items_per_page: int = Field(default=20, ge=10, le=100, description="每页显示条数")
    theme: str = Field(default="light", description="主题设置")
    
    # 搜索设置
    search_history_enabled: bool = Field(default=True, description="是否保存搜索历史")
    auto_complete_enabled: bool = Field(default=True, description="是否启用自动完成")
    
    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """用户会话模型"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    device_info: Optional[str] = Field(None, description="设备信息")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    last_active_at: datetime = Field(default_factory=datetime.utcnow, description="最后活跃时间")
    expires_at: datetime = Field(..., description="过期时间")
    
    is_active: bool = Field(default=True, description="是否活跃")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 