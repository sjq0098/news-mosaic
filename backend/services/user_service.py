"""
用户数据服务模块
提供用户数据的CRUD操作和业务逻辑
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from core.database import get_mongodb_database
from models.user import UserModel, UserUpdate, UserResponse, UserPreferences
from services.auth_service import auth_service


class UserService:
    """用户数据服务"""
    
    async def get_user_profile(self, user_id: str) -> Optional[UserResponse]:
        """获取用户档案"""
        try:
            user = await auth_service.get_user_by_id(user_id)
            if not user:
                return None
            
            # 转换为响应模型
            return UserResponse(
                id=user["_id"],
                username=user["username"],
                email=user.get("email"),
                nickname=user.get("nickname"),
                avatar_url=user.get("avatar_url"),
                bio=user.get("bio"),
                role=user.get("role", "user"),
                status=user.get("status", "active"),
                is_verified=user.get("is_verified", False),
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at"),
                last_login_at=user.get("last_login_at"),
                login_count=user.get("login_count", 0),
                search_count=user.get("search_count", 0),
                chat_count=user.get("chat_count", 0)
            )
            
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> bool:
        """更新用户档案"""
        try:
            db = await get_mongodb_database()
            if not db:
                return False
            
            # 构建更新数据
            update_fields = {}
            if update_data.nickname is not None:
                update_fields["nickname"] = update_data.nickname
            if update_data.avatar_url is not None:
                update_fields["avatar_url"] = update_data.avatar_url
            if update_data.bio is not None:
                update_fields["bio"] = update_data.bio
            if update_data.preferences is not None:
                update_fields["preferences"] = update_data.preferences
            
            update_fields["updated_at"] = datetime.utcnow()
            
            # 更新用户信息
            result = await db.users.update_one(
                {"_id": user_id},
                {"$set": update_fields}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新用户档案失败: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """获取用户偏好设置"""
        try:
            user = await auth_service.get_user_by_id(user_id)
            if not user:
                return None
            
            preferences_data = user.get("preferences", {})
            return UserPreferences(**preferences_data)
            
        except Exception as e:
            logger.error(f"获取用户偏好失败: {e}")
            return None
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """更新用户偏好设置"""
        try:
            db = await get_mongodb_database()
            if not db:
                return False
            
            # 更新偏好设置
            result = await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "preferences": preferences.dict(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False
    
    async def increment_user_stats(self, user_id: str, stat_type: str) -> bool:
        """增加用户统计数据"""
        try:
            db = await get_mongodb_database()
            if not db:
                return False
            
            # 支持的统计类型
            valid_stats = ["search_count", "chat_count", "login_count"]
            if stat_type not in valid_stats:
                return False
            
            # 增加统计数据
            result = await db.users.update_one(
                {"_id": user_id},
                {
                    "$inc": {stat_type: 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新用户统计失败: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        try:
            db = await get_mongodb_database()
            if not db:
                return False
            
            # 软删除：更新状态为已删除
            result = await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "status": "deleted",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False
    
    async def verify_user_credentials(self, username: str, password: str) -> bool:
        """验证用户凭据（用于敏感操作）"""
        try:
            user = await auth_service.get_user_by_username(username)
            if not user:
                return False
            
            return auth_service.verify_password(password, user["password_hash"])
            
        except Exception as e:
            logger.error(f"验证用户凭据失败: {e}")
            return False
    
    async def change_user_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        try:
            # 获取用户信息
            user = await auth_service.get_user_by_id(user_id)
            if not user:
                return False
            
            # 验证旧密码
            if not auth_service.verify_password(old_password, user["password_hash"]):
                return False
            
            # 生成新密码哈希
            new_password_hash = auth_service.get_password_hash(new_password)
            
            # 更新密码
            db = await get_mongodb_database()
            if not db:
                return False
            
            result = await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return False
    
    async def get_user_activity_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户活动摘要"""
        try:
            user = await auth_service.get_user_by_id(user_id)
            if not user:
                return None
            
            return {
                "user_id": user_id,
                "username": user["username"],
                "login_count": user.get("login_count", 0),
                "search_count": user.get("search_count", 0),
                "chat_count": user.get("chat_count", 0),
                "last_login_at": user.get("last_login_at"),
                "created_at": user.get("created_at"),
                "account_age_days": (datetime.utcnow() - user.get("created_at", datetime.utcnow())).days
            }
            
        except Exception as e:
            logger.error(f"获取用户活动摘要失败: {e}")
            return None


# 全局用户服务实例
user_service = UserService()
