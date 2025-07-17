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
    
    async def query_related_interests(self, user_id: str, keyword: str) -> List[str]:
        """
        智能查询与特定关键词相关的用户兴趣 - 支持语义理解
        
        Args:
            user_id: 用户ID
            keyword: 关键词
            
        Returns:
            List[str]: 相关的兴趣列表
        """
        try:
            # 获取用户当前所有兴趣
            current_interests = await self.get_user_interests(user_id)
            if not current_interests:
                return []
            
            # 构建智能语义分析提示词
            semantic_analysis_prompt = f"""你是一个语义分析专家，任务是找出与给定关键词语义相关的兴趣词汇。

**分析任务**：
给定关键词："{keyword}"
用户当前兴趣列表：{current_interests}

**分析要求**：
1. **语义关联分析**：理解关键词的深层含义和所属领域
2. **智能匹配**：找出在语义上、概念上、领域上相关的兴趣词汇
3. **举例说明**：
   - 关键词"轨道" → 应该匹配：火车、地铁、高铁、轻轨等（都属于轨道交通）
   - 关键词"球类" → 应该匹配：足球、篮球、网球等（都是球类运动）
   - 关键词"科技" → 应该匹配：AI、人工智能、大数据等（都属于科技领域）
   - 关键词"交通" → 应该匹配：汽车、火车、飞机、地铁等（都是交通工具/方式）

**输出格式**：
请直接输出相关的兴趣词汇，用英文逗号分隔。如果没有相关的兴趣，输出"无相关兴趣"。

**注意**：
- 要理解语义关联，不是简单的字符串匹配
- 考虑同义词、上下位概念、同领域概念
- 只输出用户当前兴趣列表中存在的词汇
- 不要输出解释，只输出结果

请分析："""
            
            try:
                from langchain_community.chat_models import ChatTongyi
                from langchain.schema import HumanMessage, SystemMessage
                from core.config import settings
                
                # 使用AI进行语义分析
                llm = ChatTongyi(
                    streaming=False,
                    name="qwen-turbo", 
                    dashscope_api_key=settings.DASHSCOPE_API_KEY
                )
                
                messages = [
                    SystemMessage(content="你是一个专业的语义分析专家，擅长理解词汇之间的语义关联关系。"),
                    HumanMessage(content=semantic_analysis_prompt)
                ]
                
                response = await llm.ainvoke(messages)
                analysis_result = response.content.strip()
                
                print(f"语义分析结果: {analysis_result}")
                
                # 解析AI分析结果
                if analysis_result and analysis_result != "无相关兴趣":
                    # 解析逗号分隔的词汇
                    potential_matches = [item.strip() for item in analysis_result.split(',') if item.strip()]
                    
                    # 验证这些词汇确实在用户兴趣列表中
                    related_interests = []
                    for match in potential_matches:
                        # 精确匹配或包含匹配
                        for interest in current_interests:
                            if (match.lower() == interest.lower() or 
                                match.lower() in interest.lower() or 
                                interest.lower() in match.lower()):
                                if interest not in related_interests:
                                    related_interests.append(interest)
                    
                    if related_interests:
                        logger.info(f"AI语义分析找到与 '{keyword}' 相关的兴趣: {related_interests}")
                        return related_interests
                
            except Exception as ai_error:
                logger.warning(f"AI语义分析失败: {str(ai_error)}，回退到关键词匹配")
            
            # 如果AI分析失败，回退到增强的关键词匹配
            return await self._fallback_keyword_matching(current_interests, keyword)
            
        except Exception as e:
            logger.error(f"查询相关兴趣失败: {str(e)}")
            return []

    async def _fallback_keyword_matching(self, current_interests: List[str], keyword: str) -> List[str]:
        """回退方案：增强的关键词映射匹配"""
        try:
            # 预定义的语义关联映射（作为回退方案）
            related_keywords = {
                # 交通运输领域
                "轨道": ["地铁", "轻轨", "高铁", "铁路", "轨道", "交通", "城轨", "磁悬浮", "火车", "动车", "列车", "电车"],
                "轨道交通": ["地铁", "轻轨", "高铁", "铁路", "轨道", "交通", "城轨", "磁悬浮", "火车", "动车", "列车", "电车"],
                "交通": ["地铁", "轻轨", "高铁", "铁路", "轨道", "交通", "城轨", "磁悬浮", "火车", "动车", "汽车", "飞机", "航空", "船舶", "地铁"],
                "飞机": ["飞机", "航空", "民航", "客机", "航班", "机场", "空运"],
                "汽车": ["汽车", "车辆", "轿车", "SUV", "新能源车", "电动车", "货车", "客车"],
                "火车": ["火车", "列车", "动车", "高铁", "轻轨", "地铁", "铁路", "轨道"],
                
                # 体育运动
                "体育": ["足球", "篮球", "网球", "羽毛球", "乒乓球", "游泳", "跑步", "健身", "体育", "运动", "比赛", "联赛", "奥运", "世界杯"],
                "运动": ["足球", "篮球", "网球", "羽毛球", "乒乓球", "游泳", "跑步", "健身", "体育", "运动", "比赛", "联赛"],
                "球类": ["足球", "篮球", "网球", "羽毛球", "乒乓球", "排球", "高尔夫", "棒球"],
                
                # 科技领域
                "科技": ["AI", "人工智能", "机器学习", "大数据", "云计算", "区块链", "物联网", "5G", "科技", "技术", "互联网", "芯片"],
                "AI": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "算法", "自动驾驶"],
                "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "算法", "自动驾驶"],
                
                # 娱乐文化
                "娱乐": ["电影", "电视剧", "音乐", "游戏", "综艺", "明星", "娱乐", "文化", "演唱会"],
                "文化": ["电影", "电视剧", "音乐", "文学", "艺术", "文化", "历史", "书籍"],
                
                # 财经金融
                "财经": ["股票", "基金", "投资", "理财", "金融", "经济", "市场", "银行", "证券"],
                "金融": ["股票", "基金", "投资", "理财", "金融", "经济", "银行", "保险", "证券"],
                
                # 健康医疗
                "健康": ["医疗", "健康", "养生", "保健", "疾病", "药物", "医院", "医生"],
                "医疗": ["医疗", "健康", "疾病", "药物", "医院", "医生", "治疗", "手术"],
            }
            
            # 查找相关关键词
            target_keywords = set()
            keyword_lower = keyword.lower()
            
            # 直接匹配和模糊匹配
            for key, values in related_keywords.items():
                if (keyword_lower == key.lower() or 
                    keyword_lower in key.lower() or 
                    key.lower() in keyword_lower):
                    target_keywords.update(values)
                
                # 检查是否在值列表中
                for value in values:
                    if (keyword_lower == value.lower() or
                        keyword_lower in value.lower() or 
                        value.lower() in keyword_lower):
                        target_keywords.update(values)
                        break
            
            # 如果没有预定义的关联，添加原始关键词
            if not target_keywords:
                target_keywords.add(keyword)
            
            # 在用户兴趣中查找匹配项
            related_interests = []
            for interest in current_interests:
                interest_lower = interest.lower()
                for target_keyword in target_keywords:
                    if (target_keyword.lower() in interest_lower or 
                        interest_lower in target_keyword.lower()):
                        if interest not in related_interests:
                            related_interests.append(interest)
                        break
            
            logger.info(f"回退匹配找到与 '{keyword}' 相关的兴趣: {related_interests}")
            return related_interests
            
        except Exception as e:
            logger.error(f"回退关键词匹配失败: {str(e)}")
            return []
    
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


async def clear_user_interests(user_id: str) -> bool:
    """清空用户所有兴趣的简化接口"""
    service = await get_user_interest_service()
    return await service.clear_user_interests(user_id)


async def query_related_interests(user_id: str, keyword: str) -> List[str]:
    """查询与特定关键词相关的用户兴趣的简化接口"""
    service = await get_user_interest_service()
    return await service.query_related_interests(user_id, keyword)
