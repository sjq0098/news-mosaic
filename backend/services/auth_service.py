"""
认证服务 - 处理用户认证和授权逻辑
"""

from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from passlib.context import CryptContext

from models.user import UserResponse
from services.user_service import UserService
from core.database import get_mongodb_database
from core.config import settings
from core.cache import cache, CacheKeys


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.user_service = UserService()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = getattr(settings, 'SECRET_KEY', 'your-secret-key-here')
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.db = None
    
    async def _get_db(self):
        """获取数据库连接"""
        if self.db is None:
            self.db = await get_mongodb_database()
        return self.db
    
    def _hash_password(self, password: str) -> str:
        """加密密码"""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """验证用户凭据"""
        try:
            # 获取用户信息
            user = await self.user_service.get_user_by_username(username)
            if not user:
                return None
            
            # 检查用户是否激活
            if user.status != "active":
                return None
            
            # 从数据库获取用户密码
            db = await self._get_db()
            user_data = await db.users.find_one({"username": username})
            if not user_data or "password" not in user_data:
                return None
            
            # 验证密码
            if not self._verify_password(password, user_data["password"]):
                return None
            
            return user
            
        except Exception:
            return None
    
    async def create_access_token(self, user_id: str) -> str:
        """创建访问令牌"""
        try:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            to_encode = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # 将令牌存储到缓存中
            await cache.set(
                f"{CacheKeys.USER_SESSION}{user_id}",
                encoded_jwt,
                expire=self.access_token_expire_minutes * 60
            )
            
            return encoded_jwt
            
        except Exception as e:
            raise Exception(f"创建令牌失败: {str(e)}")
    
    async def get_current_user(self, token: str) -> Optional[UserResponse]:
        """根据令牌获取当前用户"""
        try:
            # 解码令牌
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # 检查令牌是否在黑名单中
            blacklisted = await cache.get(f"blacklist:{token}")
            if blacklisted:
                return None
            
            # 获取用户信息
            user = await self.user_service.get_user_by_id(user_id)
            if not user or not user.is_active:
                return None
            
            return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
        except Exception:
            return None
    
    async def verify_password(self, user_id: str, password: str) -> bool:
        """验证用户密码"""
        try:
            db = await self._get_db()
            user_data = await db.users.find_one({"id": user_id})
            if not user_data or "password" not in user_data:
                return False
            
            return self._verify_password(password, user_data["password"])
            
        except Exception:
            return False
    
    async def change_password(self, user_id: str, new_password: str) -> bool:
        """修改用户密码"""
        try:
            db = await self._get_db()
            hashed_password = self._hash_password(new_password)
            
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "password": hashed_password,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
            
        except Exception:
            return False
    
    async def revoke_token(self, user_id: str) -> bool:
        """撤销用户令牌（登出）"""
        try:
            # 清除用户会话缓存
            await cache.delete(f"{CacheKeys.USER_SESSION}{user_id}")
            return True
            
        except Exception:
            return False
    
    async def create_user_with_password(self, username: str, email: str, password: str, full_name: str = None) -> Optional[UserResponse]:
        """创建带密码的用户"""
        try:
            # 检查用户是否已存在
            existing_user = await self.user_service.get_user_by_username(username)
            if existing_user:
                return None
            
            existing_email = await self.user_service.get_user_by_email(email)
            if existing_email:
                return None
            
            # 加密密码
            hashed_password = self._hash_password(password)
            
            # 创建用户记录
            user_id = str(secrets.token_urlsafe(16))
            now = datetime.utcnow()
            
            user_dict = {
                "id": user_id,
                "username": username,
                "email": email,
                "nickname": full_name or username,
                "bio": None,
                "role": "user",
                "status": "active",
                "is_verified": False,
                "password": hashed_password,
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
                "login_count": 0,
                "search_count": 0,
                "chat_count": 0
            }
            
            # 保存到数据库
            db = await self._get_db()
            await db.users.insert_one(user_dict)
            
            # 创建默认用户偏好
            await self.user_service._create_default_preferences(user_id)
            
            # 返回用户响应（不包含密码）
            user_response_dict = {k: v for k, v in user_dict.items() if k != "password"}
            return UserResponse(**user_response_dict)
            
        except Exception as e:
            raise Exception(f"创建用户失败: {str(e)}")
    
    async def refresh_token(self, token: str) -> Optional[str]:
        """刷新访问令牌"""
        try:
            # 验证当前令牌
            user = await self.get_current_user(token)
            if not user:
                return None
            
            # 创建新的令牌
            new_token = await self.create_access_token(user.id)
            
            # 将旧令牌加入黑名单
            await cache.set(f"blacklist:{token}", "true", expire=3600)
            
            return new_token
            
        except Exception:
            return None
    
    async def reset_password_request(self, email: str) -> bool:
        """请求重置密码"""
        try:
            user = await self.user_service.get_user_by_email(email)
            if not user:
                return False
            
            # 生成重置令牌
            reset_token = secrets.token_urlsafe(32)
            expire_time = datetime.utcnow() + timedelta(hours=1)
            
            # 存储重置令牌
            await cache.set(
                f"password_reset:{reset_token}",
                user.id,
                expire=3600  # 1小时过期
            )
            
            # 这里应该发送邮件，暂时返回True
            # TODO: 实现邮件发送功能
            
            return True
            
        except Exception:
            return False
    
    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        """重置密码"""
        try:
            # 验证重置令牌
            user_id = await cache.get(f"password_reset:{reset_token}")
            if not user_id:
                return False
            
            # 更新密码
            success = await self.change_password(user_id, new_password)
            
            if success:
                # 删除重置令牌
                await cache.delete(f"password_reset:{reset_token}")
                # 清除用户会话
                await cache.delete(f"{CacheKeys.USER_SESSION}{user_id}")
            
            return success
            
        except Exception:
            return False