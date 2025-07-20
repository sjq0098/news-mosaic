"""
数据库连接管理模块
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger
from typing import Optional

from .config import settings

# MongoDB 连接
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database = None

# SQLAlchemy 配置
Base = declarative_base()
async_engine = None
async_session_maker = None


async def init_database():
    """初始化数据库连接"""
    await init_mongodb()
    await init_mysql()


async def close_database():
    """关闭数据库连接"""
    await close_mongodb()
    await close_mysql()


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


async def init_mysql():
    """初始化 MySQL 连接"""
    global async_engine, async_session_maker
    
    try:
        # 构建连接URL
        database_url = f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        
        # 创建异步引擎
        async_engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # 创建会话工厂 - 兼容不同SQLAlchemy版本
        try:
            # 尝试使用新版本的async_sessionmaker
            from sqlalchemy.ext.asyncio import async_sessionmaker
            async_session_maker = async_sessionmaker(
                async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        except ImportError:
            # 回退到旧版本的sessionmaker
            async_session_maker = sessionmaker(
                async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        logger.info(f"MySQL 连接配置完成: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        
    except Exception as e:
        logger.error(f"MySQL 连接配置失败: {e}")
        async_engine = None
        async_session_maker = None


async def close_mysql():
    """关闭 MySQL 连接"""
    global async_engine, async_session_maker
    
    if async_engine:
        await async_engine.dispose()
        async_engine = None
        async_session_maker = None
        logger.info("MySQL 连接已关闭")


async def get_mysql_session():
    """获取 MySQL 会话"""
    if async_session_maker is None:
        raise RuntimeError("MySQL 连接未初始化")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 数据库集合/表名常量
class Collections:
    """MongoDB 集合名称"""
    NEWS = "news"
    USERS = "users"
    CONVERSATIONS = "conversations"
    USER_PREFERENCES = "user_preferences"
    SEARCH_HISTORY = "search_history"


class Tables:
    """MySQL 表名称"""
    NEWS_EMBEDDINGS = "news_embeddings"
    USER_SESSIONS = "user_sessions"
    API_LOGS = "api_logs"