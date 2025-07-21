"""
用户记忆管理服务
实现用户兴趣学习、行为分析、个性化推荐等功能
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
from pydantic import BaseModel, Field

from core.database import get_mongodb_database, Collections
from services.embedding_service import QWenEmbeddingService
from services.vector_db_service import get_vector_db


@dataclass
class UserInterest:
    """用户兴趣"""
    keyword: str
    weight: float
    category: str
    last_updated: datetime
    source: str  # 来源：search, click, like, share等


@dataclass
class UserBehavior:
    """用户行为"""
    user_id: str
    action: str  # search, click, like, share, comment等
    target_id: str  # 新闻ID、查询ID等
    timestamp: datetime
    metadata: Dict[str, Any]


class UserMemoryRequest(BaseModel):
    """用户记忆请求"""
    user_id: str = Field(..., description="用户ID")
    action: str = Field(..., description="行为类型")
    content: str = Field(..., description="内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class UserMemoryResponse(BaseModel):
    """用户记忆响应"""
    success: bool
    message: str
    user_id: str
    interests_updated: bool = False
    recommendations: List[str] = []
    personalization_score: float = 0.0


class PersonalizationRequest(BaseModel):
    """个性化请求"""
    user_id: str = Field(..., description="用户ID")
    query: Optional[str] = Field(None, description="查询内容")
    content_type: str = Field(default="news", description="内容类型")
    max_recommendations: int = Field(default=10, ge=1, le=50, description="最大推荐数量")


class PersonalizationResponse(BaseModel):
    """个性化响应"""
    success: bool
    user_id: str
    recommendations: List[Dict[str, Any]] = []
    personalized_queries: List[str] = []
    interest_profile: Dict[str, Any] = {}
    confidence_score: float = 0.0


class UserMemoryService:
    """用户记忆管理服务"""
    
    def __init__(self):
        self.embedding_service = None
        self.vector_db = None
        self.db = None
        
        # 行为权重配置
        self.behavior_weights = {
            "search": 1.0,
            "click": 2.0,
            "like": 3.0,
            "share": 4.0,
            "comment": 5.0,
            "bookmark": 6.0
        }
        
        # 兴趣衰减配置
        self.interest_decay_days = 30  # 30天后开始衰减
        self.decay_rate = 0.95  # 每天衰减5%
        
    async def _initialize_services(self):
        """初始化服务"""
        if not self.embedding_service:
            self.embedding_service = QWenEmbeddingService()
            self.vector_db = get_vector_db()
            self.db = await get_mongodb_database()
    
    async def record_user_behavior(self, request: UserMemoryRequest) -> UserMemoryResponse:
        """
        记录用户行为并更新记忆
        """
        try:
            await self._initialize_services()
            
            # 记录行为
            behavior = UserBehavior(
                user_id=request.user_id,
                action=request.action,
                target_id=request.metadata.get("target_id", ""),
                timestamp=datetime.utcnow(),
                metadata=request.metadata
            )
            
            await self._store_behavior(behavior)
            
            # 更新用户兴趣
            interests_updated = await self._update_user_interests(
                request.user_id, 
                request.content, 
                request.action
            )
            
            # 生成个性化推荐
            recommendations = await self._generate_recommendations(request.user_id)
            
            # 计算个性化分数
            personalization_score = await self._calculate_personalization_score(request.user_id)
            
            return UserMemoryResponse(
                success=True,
                message="用户行为记录成功",
                user_id=request.user_id,
                interests_updated=interests_updated,
                recommendations=recommendations,
                personalization_score=personalization_score
            )
            
        except Exception as e:
            logger.error(f"记录用户行为失败: {e}")
            return UserMemoryResponse(
                success=False,
                message=f"记录失败: {str(e)}",
                user_id=request.user_id
            )
    
    async def get_personalized_content(self, request: PersonalizationRequest) -> PersonalizationResponse:
        """
        获取个性化内容推荐
        """
        try:
            await self._initialize_services()
            
            # 获取用户兴趣档案
            interest_profile = await self._get_user_interest_profile(request.user_id)
            
            # 生成个性化查询
            personalized_queries = await self._generate_personalized_queries(
                request.user_id, 
                request.query
            )
            
            # 获取推荐内容
            recommendations = await self._get_personalized_recommendations(
                request.user_id,
                request.content_type,
                request.max_recommendations
            )
            
            # 计算置信度
            confidence_score = await self._calculate_recommendation_confidence(
                request.user_id, 
                recommendations
            )
            
            return PersonalizationResponse(
                success=True,
                user_id=request.user_id,
                recommendations=recommendations,
                personalized_queries=personalized_queries,
                interest_profile=interest_profile,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"获取个性化内容失败: {e}")
            return PersonalizationResponse(
                success=False,
                user_id=request.user_id
            )
    
    async def _store_behavior(self, behavior: UserBehavior):
        """存储用户行为"""
        behavior_doc = {
            "_id": f"{behavior.user_id}_{int(time.time() * 1000)}",
            "user_id": behavior.user_id,
            "action": behavior.action,
            "target_id": behavior.target_id,
            "timestamp": behavior.timestamp,
            "metadata": behavior.metadata
        }
        
        await self.db[Collections.API_LOGS].insert_one(behavior_doc)
    
    async def _update_user_interests(self, user_id: str, content: str, action: str) -> bool:
        """更新用户兴趣"""
        try:
            # 提取关键词
            keywords = await self._extract_keywords(content)
            if not keywords:
                return False
            
            # 获取行为权重
            weight = self.behavior_weights.get(action, 1.0)
            
            # 获取现有兴趣
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs:
                user_prefs = {
                    "user_id": user_id,
                    "interests": {},
                    "categories": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            
            # 更新兴趣权重
            interests = user_prefs.get("interests", {})
            for keyword in keywords:
                current_weight = interests.get(keyword, 0)
                interests[keyword] = current_weight + weight
            
            # 应用兴趣衰减
            interests = await self._apply_interest_decay(interests)
            
            # 保持兴趣数量在合理范围内
            if len(interests) > 100:
                # 保留权重最高的100个兴趣
                sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
                interests = dict(sorted_interests[:100])
            
            user_prefs["interests"] = interests
            user_prefs["updated_at"] = datetime.utcnow()
            
            # 更新数据库
            await self.db[Collections.USER_PREFERENCES].replace_one(
                {"user_id": user_id},
                user_prefs,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新用户兴趣失败: {e}")
            return False
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，实际项目中可以使用更复杂的NLP技术
        import re
        
        # 清理文本
        content = re.sub(r'[^\w\s]', ' ', content.lower())
        words = content.split()
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 返回前20个关键词
        return keywords[:20]
    
    async def _apply_interest_decay(self, interests: Dict[str, float]) -> Dict[str, float]:
        """应用兴趣衰减"""
        current_time = datetime.utcnow()
        decayed_interests = {}
        
        for keyword, weight in interests.items():
            # 简单的时间衰减模型
            # 实际项目中可以记录每个兴趣的最后更新时间
            decayed_weight = weight * 0.99  # 每次更新时轻微衰减
            if decayed_weight > 0.1:  # 保留有意义的兴趣
                decayed_interests[keyword] = decayed_weight
        
        return decayed_interests
    
    async def _generate_recommendations(self, user_id: str) -> List[str]:
        """生成推荐查询"""
        try:
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs or not user_prefs.get("interests"):
                return ["热门新闻", "科技资讯", "财经动态"]
            
            # 获取用户最感兴趣的话题
            interests = user_prefs["interests"]
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:5]
            
            recommendations = []
            for interest, _ in top_interests:
                recommendations.append(f"{interest}最新动态")
                recommendations.append(f"{interest}深度分析")
            
            return recommendations[:10]
            
        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            return ["推荐新闻", "热点话题"]
    
    async def _calculate_personalization_score(self, user_id: str) -> float:
        """计算个性化分数"""
        try:
            # 基于用户行为数据计算个性化程度
            behavior_count = await self.db[Collections.API_LOGS].count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
            })
            
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            interest_count = len(user_prefs.get("interests", {})) if user_prefs else 0
            
            # 简单的评分模型
            behavior_score = min(behavior_count / 100.0, 1.0)  # 行为数量评分
            interest_score = min(interest_count / 50.0, 1.0)   # 兴趣数量评分
            
            return (behavior_score + interest_score) / 2.0
            
        except Exception as e:
            logger.error(f"计算个性化分数失败: {e}")
            return 0.0
    
    async def _get_user_interest_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户兴趣档案"""
        try:
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs:
                return {}
            
            interests = user_prefs.get("interests", {})
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "top_interests": [{"keyword": k, "weight": v} for k, v in top_interests],
                "total_interests": len(interests),
                "last_updated": user_prefs.get("updated_at"),
                "profile_strength": await self._calculate_personalization_score(user_id)
            }
            
        except Exception as e:
            logger.error(f"获取用户兴趣档案失败: {e}")
            return {}
    
    async def _generate_personalized_queries(self, user_id: str, base_query: Optional[str] = None) -> List[str]:
        """生成个性化查询"""
        try:
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs or not user_prefs.get("interests"):
                return []
            
            interests = user_prefs["interests"]
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:3]
            
            queries = []
            for interest, _ in top_interests:
                if base_query:
                    queries.append(f"{base_query} {interest}")
                else:
                    queries.append(f"{interest}最新新闻")
            
            return queries
            
        except Exception as e:
            logger.error(f"生成个性化查询失败: {e}")
            return []
    
    async def _get_personalized_recommendations(self, user_id: str, content_type: str, max_count: int) -> List[Dict[str, Any]]:
        """获取个性化推荐内容"""
        try:
            # 基于用户兴趣从数据库中查找相关内容
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs or not user_prefs.get("interests"):
                return []
            
            interests = user_prefs["interests"]
            top_keywords = list(sorted(interests.items(), key=lambda x: x[1], reverse=True)[:5])
            
            recommendations = []
            for keyword, weight in top_keywords:
                # 搜索包含关键词的新闻
                news_items = await self.db[Collections.NEWS].find({
                    "$or": [
                        {"title": {"$regex": keyword, "$options": "i"}},
                        {"content": {"$regex": keyword, "$options": "i"}}
                    ]
                }).limit(2).to_list(length=2)
                
                for news in news_items:
                    recommendations.append({
                        "id": news["_id"],
                        "title": news["title"],
                        "content": news.get("content", "")[:200],
                        "url": news.get("url"),
                        "source": news.get("source"),
                        "relevance_score": weight,
                        "reason": f"基于您对'{keyword}'的兴趣"
                    })
            
            # 按相关性排序并限制数量
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
            return recommendations[:max_count]
            
        except Exception as e:
            logger.error(f"获取个性化推荐失败: {e}")
            return []
    
    async def _calculate_recommendation_confidence(self, user_id: str, recommendations: List[Dict[str, Any]]) -> float:
        """计算推荐置信度"""
        try:
            if not recommendations:
                return 0.0
            
            # 基于推荐数量和用户档案强度计算置信度
            profile_strength = await self._calculate_personalization_score(user_id)
            recommendation_count = len(recommendations)
            
            # 简单的置信度模型
            count_factor = min(recommendation_count / 10.0, 1.0)
            confidence = (profile_strength + count_factor) / 2.0
            
            return confidence
            
        except Exception as e:
            logger.error(f"计算推荐置信度失败: {e}")
            return 0.0


# 全局实例
user_memory_service = UserMemoryService()


async def get_user_memory_service() -> UserMemoryService:
    """获取用户记忆服务实例"""
    return user_memory_service
