"""
个性化推荐服务模块
基于用户偏好和行为提供个性化新闻推荐
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from core.database import get_mongodb_database
from services.user_service import user_service
from models.user import UserPreferences


class PersonalizationService:
    """个性化推荐服务"""
    
    def __init__(self):
        self.default_categories = ["科技", "财经", "社会", "国际"]
        self.default_sources = ["新华网", "人民网", "央视新闻"]
    
    async def get_personalized_news_query(self, user_id: str) -> Dict[str, Any]:
        """
        根据用户偏好生成个性化新闻查询参数
        """
        try:
            # 获取用户偏好
            preferences = await user_service.get_user_preferences(user_id)
            if not preferences:
                preferences = UserPreferences()
            
            # 构建查询参数
            query_params = {}
            
            # 关键词偏好
            if preferences.news_interests:
                query_params["keywords"] = preferences.news_interests[:5]  # 限制关键词数量
            
            # 分类偏好
            if preferences.preferred_categories:
                query_params["categories"] = preferences.preferred_categories
            else:
                query_params["categories"] = self.default_categories
            
            # 来源偏好
            if preferences.preferred_sources:
                query_params["sources"] = preferences.preferred_sources
            else:
                query_params["sources"] = self.default_sources
            
            # 语言偏好
            query_params["language"] = preferences.language or "zh-CN"
            
            # 分页设置
            query_params["limit"] = preferences.items_per_page or 20
            
            return query_params
            
        except Exception as e:
            logger.error(f"生成个性化查询失败: {e}")
            return {
                "categories": self.default_categories,
                "sources": self.default_sources,
                "language": "zh-CN",
                "limit": 20
            }
    
    async def record_user_interaction(self, user_id: str, interaction_type: str, content_id: str, metadata: Optional[Dict] = None):
        """
        记录用户交互行为
        """
        try:
            db = await get_mongodb_database()
            if not db:
                return False
            
            interaction = {
                "user_id": user_id,
                "interaction_type": interaction_type,  # view, like, share, comment, search
                "content_id": content_id,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            await db.user_interactions.insert_one(interaction)
            
            # 更新用户统计
            if interaction_type == "search":
                await user_service.increment_user_stats(user_id, "search_count")
            elif interaction_type == "view":
                # 可以添加阅读统计
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"记录用户交互失败: {e}")
            return False
    
    async def get_user_reading_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户阅读历史
        """
        try:
            db = await get_mongodb_database()
            if not db:
                return []
            
            # 查询用户的阅读记录
            cursor = db.user_interactions.find(
                {
                    "user_id": user_id,
                    "interaction_type": {"$in": ["view", "like", "share"]}
                }
            ).sort("timestamp", -1).limit(limit)
            
            history = []
            async for interaction in cursor:
                history.append({
                    "content_id": interaction["content_id"],
                    "interaction_type": interaction["interaction_type"],
                    "timestamp": interaction["timestamp"],
                    "metadata": interaction.get("metadata", {})
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取用户阅读历史失败: {e}")
            return []
    
    async def get_trending_topics(self, user_id: Optional[str] = None) -> List[str]:
        """
        获取热门话题（可基于用户偏好个性化）
        """
        try:
            db = await get_mongodb_database()
            if not db:
                return ["科技创新", "经济发展", "社会热点", "国际新闻"]
            
            # 基于用户交互数据分析热门话题
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)},
                        "interaction_type": {"$in": ["view", "search", "like"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.category",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 10
                }
            ]
            
            if user_id:
                # 如果提供了用户ID，可以基于用户偏好调整权重
                preferences = await user_service.get_user_preferences(user_id)
                if preferences and preferences.preferred_categories:
                    # 为用户偏好的分类增加权重
                    pipeline[0]["$match"]["$or"] = [
                        {"metadata.category": {"$in": preferences.preferred_categories}},
                        {}
                    ]
            
            cursor = db.user_interactions.aggregate(pipeline)
            topics = []
            async for result in cursor:
                if result["_id"]:
                    topics.append(result["_id"])
            
            # 如果没有足够的数据，返回默认话题
            if len(topics) < 5:
                default_topics = ["科技创新", "经济发展", "社会热点", "国际新闻", "文化教育"]
                topics.extend([t for t in default_topics if t not in topics])
            
            return topics[:10]
            
        except Exception as e:
            logger.error(f"获取热门话题失败: {e}")
            return ["科技创新", "经济发展", "社会热点", "国际新闻"]
    
    async def get_recommended_keywords(self, user_id: str) -> List[str]:
        """
        基于用户行为推荐关键词
        """
        try:
            db = await get_mongodb_database()
            if not db:
                return []
            
            # 分析用户搜索历史
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "interaction_type": "search",
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.query",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 10
                }
            ]
            
            cursor = db.user_interactions.aggregate(pipeline)
            keywords = []
            async for result in cursor:
                if result["_id"]:
                    keywords.append(result["_id"])
            
            return keywords
            
        except Exception as e:
            logger.error(f"获取推荐关键词失败: {e}")
            return []
    
    async def update_user_interests_from_behavior(self, user_id: str):
        """
        基于用户行为自动更新兴趣偏好
        """
        try:
            # 获取用户最近的交互数据
            db = await get_mongodb_database()
            if not db:
                return False
            
            # 分析最近30天的行为
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)},
                        "interaction_type": {"$in": ["view", "like", "share"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.category",
                        "score": {
                            "$sum": {
                                "$switch": {
                                    "branches": [
                                        {"case": {"$eq": ["$interaction_type", "like"]}, "then": 3},
                                        {"case": {"$eq": ["$interaction_type", "share"]}, "then": 2},
                                        {"case": {"$eq": ["$interaction_type", "view"]}, "then": 1}
                                    ],
                                    "default": 1
                                }
                            }
                        }
                    }
                },
                {
                    "$sort": {"score": -1}
                },
                {
                    "$limit": 5
                }
            ]
            
            cursor = db.user_interactions.aggregate(pipeline)
            new_interests = []
            async for result in cursor:
                if result["_id"] and result["score"] > 5:  # 只有足够活跃的分类才加入兴趣
                    new_interests.append(result["_id"])
            
            if new_interests:
                # 获取当前偏好
                preferences = await user_service.get_user_preferences(user_id)
                if preferences:
                    # 合并新兴趣和现有兴趣
                    current_interests = set(preferences.news_interests or [])
                    current_interests.update(new_interests)
                    
                    # 更新偏好
                    preferences.news_interests = list(current_interests)[:10]  # 限制数量
                    await user_service.update_user_preferences(user_id, preferences)
                    
                    logger.info(f"用户 {user_id} 的兴趣偏好已自动更新: {new_interests}")
            
            return True
            
        except Exception as e:
            logger.error(f"自动更新用户兴趣失败: {e}")
            return False


# 全局个性化服务实例
personalization_service = PersonalizationService()
