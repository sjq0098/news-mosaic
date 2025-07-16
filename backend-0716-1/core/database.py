"""
数据库连接管理模块（仅MongoDB）
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# MongoDB 连接
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database = None


async def init_database():
    """初始化数据库连接（仅MongoDB）"""
    await init_mongodb()


async def close_database():
    """关闭数据库连接（仅MongoDB）"""
    await close_mongodb()


async def init_mongodb():
    """初始化 MongoDB 连接"""
    global mongodb_client, mongodb_database
    
    try:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb_database = mongodb_client[settings.MONGODB_DB_NAME]
        
        # 测试连接
        await mongodb_client.admin.command('ping')
        logger.info(f"MongoDB 连接成功: {settings.MONGODB_URL}")
        
    except Exception as e:
        logger.error(f"MongoDB 连接失败: {e}")
        mongodb_client = None
        mongodb_database = None


async def close_mongodb():
    """关闭 MongoDB 连接"""
    global mongodb_client, mongodb_database
    
    if mongodb_client:
        mongodb_client.close()
        mongodb_client = None
        mongodb_database = None
        logger.info("MongoDB 连接已关闭")


async def get_mongodb_database():
    """获取 MongoDB 数据库实例，如果未连接则自动初始化"""
    global mongodb_database
    
    if mongodb_database is None:
        await init_mongodb()
    
    return mongodb_database


# 数据库集合/表名常量
class Collections:
    """MongoDB 集合名称"""
    NEWS = "news"
    USERS = "users"
    USER_SESSIONS = "user_sessions"  # 用户会话表
    CONVERSATIONS = "conversations"
    USER_PREFERENCES = "user_preferences"
    SEARCH_HISTORY = "search_history" 