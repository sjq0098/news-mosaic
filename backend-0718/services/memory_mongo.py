"""
会话记忆存储服务
基于MongoDB的会话级记忆管理
"""

from typing import Optional, Dict, Any
from pymongo import MongoClient


class SessionMemoryStore:
    """会话级记忆存储：每个 session_id 独立存储记忆内容"""
    
    def __init__(
        self, 
        mongo_uri: str = "mongodb://localhost:27017/", 
        db_name: str = "news_mosaic", 
        collection_name: str = "session_memory"
    ) -> None:
        """
        初始化会话记忆存储
        
        Args:
            mongo_uri: MongoDB连接URI
            db_name: 数据库名称
            collection_name: 集合名称
        """
        self.client = MongoClient(mongo_uri)
        self.collection = self.client[db_name][collection_name]

    def get_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定会话的记忆内容
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 记忆内容，不存在则返回None
        """
        doc = self.collection.find_one({"_id": session_id})
        return doc["memory"] if doc and "memory" in doc else None

    def save_memory(self, session_id: str, memory: Dict[str, Any]) -> None:
        """
        保存/更新指定会话的记忆内容
        
        Args:
            session_id: 会话ID
            memory: 记忆内容
        """
        self.collection.update_one(
            {"_id": session_id},
            {"$set": {"memory": memory}},
            upsert=True
        )

    def clear_memory(self, session_id: str) -> None:
        """
        清除指定会话的记忆
        
        Args:
            session_id: 会话ID
        """
        self.collection.delete_one({"_id": session_id})
