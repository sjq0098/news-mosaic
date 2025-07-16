"""
用户兴趣管理服务模块
专门处理用户新闻兴趣的增删改查操作
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from core.database import get_mongodb_database, Collections
from models.user import UserPreferences

logger = logging.getLogger(__name__)


class UserInterestService:
    """用户兴趣管理服务"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    async def add_user_interests(self, user_id: str, new_interests: List[str]) -> bool:
        """
        添加用户兴趣
        
        Args:
            user_id: 用户ID
            new_interests: 新增兴趣列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return False
            
            users_collection = db[Collections.USERS]
            
            # 将字符串ID转换为ObjectId
            try:
                object_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            except Exception as e:
                logger.error(f"无效的用户ID格式: {user_id}, 错误: {e}")
                return False
                
            user_doc = await users_collection.find_one({"_id": object_id})
            
            if not user_doc:
                logger.warning(f"用户不存在: {user_id}")
                return False
            
            # 获取现有兴趣
            existing_preferences = user_doc.get("news_preferences", {})
            existing_interests = set(existing_preferences.get("news_interests", []))
            
            # 合并新兴趣
            updated_interests = list(existing_interests.union(set(new_interests)))
            
            # 限制数量（最多20个兴趣）
            if len(updated_interests) > 20:
                updated_interests = updated_interests[-20:]
            
            # 更新数据库
            updated_preferences = UserPreferences(news_interests=updated_interests)
            
            result = await users_collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "news_preferences": updated_preferences.dict(),
                        "updated_at": datetime.now()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"成功为用户 {user_id} 添加兴趣: {new_interests}")
            else:
                logger.warning(f"用户 {user_id} 兴趣添加未生效")
            
            return success
            
        except Exception as e:
            logger.error(f"添加用户兴趣失败: {str(e)}")
            return False
    
    async def remove_user_interests(self, user_id: str, interests_to_remove: List[str]) -> bool:
        """
        移除用户兴趣
        
        Args:
            user_id: 用户ID
            interests_to_remove: 要移除的兴趣列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return False
            
            users_collection = db[Collections.USERS]
            
            # 将字符串ID转换为ObjectId
            try:
                object_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            except Exception as e:
                logger.error(f"无效的用户ID格式: {user_id}, 错误: {e}")
                return False
                
            user_doc = await users_collection.find_one({"_id": object_id})
            
            if not user_doc:
                logger.warning(f"用户不存在: {user_id}")
                return False
            
            # 获取现有兴趣
            existing_preferences = user_doc.get("news_preferences", {})
            existing_interests = set(existing_preferences.get("news_interests", []))
            
            # 移除指定兴趣
            updated_interests = list(existing_interests - set(interests_to_remove))
            
            # 更新数据库
            updated_preferences = UserPreferences(news_interests=updated_interests)
            
            result = await users_collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "news_preferences": updated_preferences.dict(),
                        "updated_at": datetime.now()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"成功为用户 {user_id} 移除兴趣: {interests_to_remove}")
            else:
                logger.warning(f"用户 {user_id} 兴趣移除未生效")
            
            return success
            
        except Exception as e:
            logger.error(f"移除用户兴趣失败: {str(e)}")
            return False
    
    async def get_user_interests(self, user_id: str) -> Optional[List[str]]:
        """
        获取用户兴趣列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[List[str]]: 用户兴趣列表，失败时返回None
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return None
            
            users_collection = db[Collections.USERS]
            
            # 将字符串ID转换为ObjectId
            try:
                object_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            except Exception as e:
                logger.error(f"无效的用户ID格式: {user_id}, 错误: {e}")
                return None
                
            user_doc = await users_collection.find_one({"_id": object_id})
            
            if not user_doc:
                logger.warning(f"用户不存在: {user_id}")
                return None
            
            preferences = user_doc.get("news_preferences", {})
            interests = preferences.get("news_interests", [])
            
            logger.info(f"获取用户 {user_id} 兴趣列表: {interests}")
            return interests
            
        except Exception as e:
            logger.error(f"获取用户兴趣失败: {str(e)}")
            return None
    
    async def clear_user_interests(self, user_id: str) -> bool:
        """
        清空用户所有兴趣
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return False
            
            users_collection = db[Collections.USERS]
            
            # 将字符串ID转换为ObjectId
            try:
                object_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            except Exception as e:
                logger.error(f"无效的用户ID格式: {user_id}, 错误: {e}")
                return False
            
            # 清空兴趣列表
            updated_preferences = UserPreferences(news_interests=[])
            
            result = await users_collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "news_preferences": updated_preferences.dict(),
                        "updated_at": datetime.now()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"成功清空用户 {user_id} 的所有兴趣")
            
            return success
            
        except Exception as e:
            logger.error(f"清空用户兴趣失败: {str(e)}")
            return False
    
    async def get_interest_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户兴趣统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            interests = await self.get_user_interests(user_id)
            if interests is None:
                return {"error": "获取失败"}
            
            return {
                "total_interests": len(interests),
                "interests": interests,
                "max_allowed": 20,
                "can_add_more": len(interests) < 20
            }
            
        except Exception as e:
            logger.error(f"获取兴趣统计失败: {str(e)}")
            return {"error": str(e)}


# 全局服务实例
_user_interest_service: Optional[UserInterestService] = None


async def get_user_interest_service() -> UserInterestService:
    """获取用户兴趣管理服务实例（单例模式）"""
    global _user_interest_service
    if _user_interest_service is None:
        _user_interest_service = UserInterestService()
    return _user_interest_service


# 为方便调用提供的简化函数
async def add_user_interests(user_id: str, interests: List[str]) -> bool:
    """添加用户兴趣的简化接口"""
    service = await get_user_interest_service()
    return await service.add_user_interests(user_id, interests)


async def remove_user_interests(user_id: str, interests: List[str]) -> bool:
    """移除用户兴趣的简化接口"""
    service = await get_user_interest_service()
    return await service.remove_user_interests(user_id, interests)


async def get_user_interests(user_id: str) -> Optional[List[str]]:
    """获取用户兴趣的简化接口"""
    service = await get_user_interest_service()
    return await service.get_user_interests(user_id)
