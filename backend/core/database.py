"""
数据库连接管理模块
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from typing import Optional

from .config import settings

# MongoDB 连接
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database = None


async def init_database():
    """初始化数据库连接"""
    await init_mongodb()


async def close_database():
    """关闭数据库连接"""
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
    """获取 MongoDB 数据库实例"""
    return mongodb_database





# 数据库集合名常量
class Collections:
    """MongoDB 集合名称"""
    NEWS = "news"
    USERS = "users"
    CONVERSATIONS = "conversations"
    USER_PREFERENCES = "user_preferences"
    SEARCH_HISTORY = "search_history"
    NEWS_EMBEDDINGS = "news_embeddings"
    USER_SESSIONS = "user_sessions"
    API_LOGS = "api_logs"