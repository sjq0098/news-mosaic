"""
用户认证服务模块
提供用户注册、登录、JWT token 生成和验证等功能
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger

from core.config import settings
from core.database import get_mongodb_database
from models.user import (
    UserModel, UserCreate, UserLogin, UserResponse, UserPreferences,
    UserCreateRequest, UserLoginRequest, UserCreateResult, UserLoginResult
)


class AuthService:
    """用户认证服务"""
    
    def __init__(self):
        # 密码加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Token验证失败: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return None
            
            user = await db.users.find_one({"username": username})
            return user
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return None

            user = await db.users.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return None

            user = await db.users.find_one({"_id": user_id})
            return user
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    async def create_user(self, user_data: UserCreateRequest) -> UserCreateResult:
        """创建用户"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return UserCreateResult(
                    status="error",
                    message="数据库连接失败",
                    user_id=""
                )
            
            # 检查用户名是否已存在
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                return UserCreateResult(
                    status="error",
                    message="用户名已存在",
                    user_id=""
                )
            
            # 检查邮箱是否已存在
            if user_data.email:
                existing_email = await self.get_user_by_email(user_data.email)
                if existing_email:
                    return UserCreateResult(
                        status="error",
                        message="邮箱已被注册",
                        user_id=""
                    )
            
            # 生成用户ID
            user_id = secrets.token_urlsafe(16)
            
            # 创建用户文档
            user_doc = {
                "_id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "password_hash": self.get_password_hash(user_data.password),
                "nickname": user_data.nickname or user_data.username,
                "bio": user_data.bio,
                "avatar_url": None,
                "role": "user",
                "status": "active",
                "is_verified": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login_at": None,
                "login_count": 0,
                "search_count": 0,
                "chat_count": 0,
                "preferences": UserPreferences().dict()
            }
            
            # 插入用户文档
            result = await db.users.insert_one(user_doc)
            
            if result.inserted_id:
                logger.info(f"用户创建成功: {user_data.username}")
                return UserCreateResult(
                    status="success",
                    message="用户创建成功",
                    user_id=user_id
                )
            else:
                return UserCreateResult(
                    status="error",
                    message="用户创建失败",
                    user_id=""
                )
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return UserCreateResult(
                status="error",
                message=f"创建用户失败: {str(e)}",
                user_id=""
            )
    
    async def login_user(self, login_data: UserLoginRequest) -> UserLoginResult:
        """用户登录"""
        try:
            # 获取用户信息
            user = await self.get_user_by_username(login_data.username)
            if not user:
                # 尝试通过邮箱查找
                user = await self.get_user_by_email(login_data.username)
            
            if not user:
                return UserLoginResult(
                    status="error",
                    message="用户不存在",
                    user_id="",
                    username="",
                    sessions=[]
                )
            
            # 验证密码
            if not self.verify_password(login_data.password, user["password_hash"]):
                return UserLoginResult(
                    status="error",
                    message="密码错误",
                    user_id="",
                    username="",
                    sessions=[]
                )
            
            # 检查用户状态
            if user.get("status") != "active":
                return UserLoginResult(
                    status="error",
                    message="账户已被禁用",
                    user_id="",
                    username="",
                    sessions=[]
                )
            
            # 生成令牌
            token_data = {
                "sub": user["_id"],
                "username": user["username"],
                "email": user.get("email"),
                "role": user.get("role", "user")
            }
            
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)
            
            # 更新登录信息
            db = await get_mongodb_database()
            if db is not None:
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "last_login_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        },
                        "$inc": {"login_count": 1}
                    }
                )
            
            logger.info(f"用户登录成功: {user['username']}")
            return UserLoginResult(
                status="success",
                message="登录成功",
                user_id=user["_id"],
                username=user["username"],
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                sessions=[]  # TODO: 实现会话管理
            )
            
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return UserLoginResult(
                status="error",
                message=f"登录失败: {str(e)}",
                user_id="",
                username="",
                sessions=[]
            )


# 全局认证服务实例
auth_service = AuthService()
