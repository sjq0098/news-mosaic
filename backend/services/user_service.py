"""
用户服务 - 处理用户相关的业务逻辑
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from models.user import (
    UserModel, UserCreate, UserUpdate, UserResponse, 
    UserPreferences
)
from core.database import get_mongodb_database
from core.config import settings


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """获取数据库连接"""
        if self.db is None:
            self.db = await get_mongodb_database()
        return self.db
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建新用户"""
        try:
            db = await self._get_db()
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # 创建用户记录
            user_dict = {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "nickname": user_data.nickname,
                "bio": user_data.bio,
                "role": "user",
                "status": "active",
                "is_verified": False,
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
                "login_count": 0,
                "search_count": 0,
                "chat_count": 0
            }
            
            # 保存到数据库
            await db.users.insert_one(user_dict)
            
            # 创建默认用户偏好
            await self._create_default_preferences(user_id)
            
            return UserResponse(**user_dict)
            
        except Exception as e:
            raise Exception(f"创建用户失败: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        try:
            db = await self._get_db()
            user = await db.users.find_one({"id": user_id})
            if user:
                return UserResponse(**user)
            return None
        except Exception:
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """根据用户名获取用户"""
        try:
            db = await self._get_db()
            user = await db.users.find_one({"username": username})
            if user:
                return UserResponse(**user)
            return None
        except Exception:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户"""
        try:
            db = await self._get_db()
            user = await db.users.find_one({"email": email})
            if user:
                return UserResponse(**user)
            return None
        except Exception:
            return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
        """更新用户信息"""
        try:
            db = await self._get_db()
            update_dict = user_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
            return None
            
        except Exception:
            return None
    
    async def update_last_login(self, user_id: str) -> bool:
        """更新最后登录时间"""
        try:
            db = await self._get_db()
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": {"last_login_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            db = await self._get_db()
            # 删除用户相关数据
            await db.user_preferences.delete_one({"user_id": user_id})
            await db.user_stats.delete_one({"user_id": user_id})
            
            # 删除用户
            result = await db.users.delete_one({"id": user_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """获取用户偏好设置"""
        try:
            db = await self._get_db()
            prefs = await db.user_preferences.find_one({"user_id": user_id})
            if prefs:
                return UserPreferences(**prefs)
            
            # 如果没有偏好设置，创建默认的
            return await self._create_default_preferences(user_id)
            
        except Exception:
            return await self._create_default_preferences(user_id)
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> UserPreferences:
        """更新用户偏好设置"""
        try:
            db = await self._get_db()
            prefs_dict = preferences.dict()
            prefs_dict["user_id"] = user_id
            prefs_dict["updated_at"] = datetime.utcnow()
            
            await db.user_preferences.update_one(
                {"user_id": user_id},
                {"$set": prefs_dict},
                upsert=True
            )
            
            return preferences
            
        except Exception as e:
            raise Exception(f"更新用户偏好失败: {str(e)}")
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            db = await self._get_db()
            stats = await db.user_stats.find_one({"user_id": user_id})
            if not stats:
                # 创建默认统计信息
                stats = {
                    "user_id": user_id,
                    "articles_read": 0,
                    "searches_performed": 0,
                    "chats_started": 0,
                    "total_time_spent": 0,
                    "favorite_categories": [],
                    "created_at": datetime.utcnow()
                }
                await db.user_stats.insert_one(stats)
            
            return {
                "articles_read": stats.get("articles_read", 0),
                "searches_performed": stats.get("searches_performed", 0),
                "chats_started": stats.get("chats_started", 0),
                "total_time_spent": stats.get("total_time_spent", 0),
                "favorite_categories": stats.get("favorite_categories", [])
            }
            
        except Exception:
            return {
                "articles_read": 0,
                "searches_performed": 0,
                "chats_started": 0,
                "total_time_spent": 0,
                "favorite_categories": []
            }
    
    async def get_all_users(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取所有用户（分页）"""
        try:
            db = await self._get_db()
            skip = (page - 1) * size
            
            users_cursor = db.users.find().skip(skip).limit(size)
            users = []
            async for user in users_cursor:
                users.append(UserResponse(**user))
            
            total = await db.users.count_documents({})
            
            return {
                "users": users,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
            
        except Exception as e:
            raise Exception(f"获取用户列表失败: {str(e)}")
    
    async def update_user_status(self, user_id: str, status: str) -> bool:
        """更新用户状态"""
        try:
            db = await self._get_db()
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": {"is_active": status == "active", "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def _create_default_preferences(self, user_id: str) -> UserPreferences:
        """创建默认用户偏好设置"""
        db = await self._get_db()
        default_prefs = UserPreferences(
            preferred_categories=["technology", "business"],
            preferred_sources=["综合"],
            language="zh-CN",
            timezone="Asia/Shanghai",
            email_notifications=True,
            push_notifications=True,
            items_per_page=20,
            theme="light",
            search_history_enabled=True,
            auto_complete_enabled=True
        )
        
        prefs_dict = default_prefs.dict()
        prefs_dict["user_id"] = user_id
        prefs_dict["created_at"] = datetime.utcnow()
        prefs_dict["updated_at"] = datetime.utcnow()
        
        await db.user_preferences.insert_one(prefs_dict)
        
        return default_prefs