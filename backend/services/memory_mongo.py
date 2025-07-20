"""
会话记忆存储服务
基于MongoDB的会话级记忆管理
"""

from typing import Optional, Dict, Any
from core.database import get_mongodb_database
import logging
import asyncio

logger = logging.getLogger(__name__)

class SessionMemoryStore:
    """会话级记忆存储：每个 session_id 独立存储记忆内容"""

    def __init__(self) -> None:
        """
        初始化会话记忆存储
        """
        self.collection_name = "session_memory"

    def get_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定会话的记忆内容（同步接口）

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 记忆内容，不存在则返回None
        """
        try:
            # 尝试在当前事件循环中运行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，创建一个任务
                future = asyncio.create_task(self._get_memory_async(session_id))
                # 注意：这里不能直接等待，返回None作为fallback
                return None
            else:
                # 如果不在异步环境中，创建新的事件循环
                return asyncio.run(self._get_memory_async(session_id))
        except Exception as e:
            logger.error(f"获取会话记忆失败: {str(e)}")
            return None

    async def _get_memory_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定会话的记忆内容（异步版本）

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 记忆内容，不存在则返回None
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return None
                
            collection = db[self.collection_name]
            doc = await collection.find_one({"_id": session_id})
            return doc["memory"] if doc and "memory" in doc else None
            
        except Exception as e:
            logger.error(f"获取会话记忆失败: {str(e)}")
            return None

    def save_memory(self, session_id: str, memory: Dict[str, Any]) -> None:
        """
        保存/更新指定会话的记忆内容（同步接口）

        Args:
            session_id: 会话ID
            memory: 记忆内容
        """
        try:
            # 尝试在当前事件循环中运行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，创建一个任务
                asyncio.create_task(self._save_memory_async(session_id, memory))
            else:
                # 如果不在异 asynchronous 环境中，创建新的事件循环
                asyncio.run(self._save_memory_async(session_id, memory))
        except Exception as e:
            logger.error(f"保存会话记忆失败: {str(e)}")
    
    async def _save_memory_async(self, session_id: str, memory: Dict[str, Any]) -> None:
        """
        保存/更新指定会话的记忆内容（异步版本）

        Args:
            session_id: 会话ID
            memory: 记忆内容
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return
                
            collection = db[self.collection_name]
            await collection.update_one(
                {"_id": session_id},
                {"$set": {"memory": memory}},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"保存会话记忆失败: {str(e)}")

    def clear_memory(self, session_id: str) -> None:
        """
        清除指定会话的记忆（同步接口）

        Args:
            session_id: 会话ID
        """
        try:
            # 尝试在当前事件循环中运行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，创建一个任务
                asyncio.create_task(self._clear_memory_async(session_id))
            else:
                # 如果不在异步环境中，创建新的事件循环
                asyncio.run(self._clear_memory_async(session_id))
        except Exception as e:
            logger.error(f"清除会话记忆失败: {str(e)}")
    
    async def _clear_memory_async(self, session_id: str) -> None:
        """
        清除指定会话的记忆（异步版本）

        Args:
            session_id: 会话ID
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return
                
            collection = db[self.collection_name]
            await collection.delete_one({"_id": session_id})
            
        except Exception as e:
            logger.error(f"清除会话记忆失败: {str(e)}")