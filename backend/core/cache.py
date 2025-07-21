"""
Redis 缓存管理模块
"""

import redis.asyncio as aioredis
import json
from typing import Any, Optional, Union
from loguru import logger

from .config import settings

# Redis 连接池
redis_pool: Optional[aioredis.Redis] = None


async def init_redis():
    """初始化 Redis 连接"""
    global redis_pool
    
    try:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
        
        # 测试连接
        await redis_pool.ping()
        logger.info(f"Redis 连接成功: {settings.REDIS_URL}")
        
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        redis_pool = None


async def close_redis():
    """关闭 Redis 连接"""
    global redis_pool
    
    if redis_pool:
        await redis_pool.close()
        redis_pool = None
        logger.info("Redis 连接已关闭")


async def get_redis():
    """获取 Redis 连接"""
    return redis_pool


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis = None
    
    async def _get_redis(self):
        """获取 Redis 连接"""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                await redis.setex(key, expire, value)
            else:
                await redis.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return None
            
            value = await redis.get(key)
            if value is None:
                return None
            
            # 尝试反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            result = await redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            result = await redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            result = await redis.expire(key, seconds)
            return result
            
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False
    
    async def keys(self, pattern: str) -> list:
        """获取匹配模式的键列表"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return []
            
            keys = await redis.keys(pattern)
            return keys
            
        except Exception as e:
            logger.error(f"获取键列表失败 {pattern}: {e}")
            return []
    
    async def flush_pattern(self, pattern: str) -> int:
        """清空匹配模式的缓存"""
        try:
            keys = await self.keys(pattern)
            if not keys:
                return 0
            
            redis = await self._get_redis()
            if redis is None:
                return 0
            
            result = await redis.delete(*keys)
            logger.info(f"清空缓存模式 {pattern}: {result} 个键")
            return result
            
        except Exception as e:
            logger.error(f"清空缓存模式失败 {pattern}: {e}")
            return 0


# 创建全局缓存管理器实例
cache = CacheManager()


# 缓存键前缀常量
class CacheKeys:
    """缓存键常量"""
    NEWS_SEARCH = "news:search:"
    NEWS_DETAIL = "news:detail:"
    USER_SESSION = "user:session:"
    USER_PREFERENCES = "user:preferences:"
    CHAT_HISTORY = "chat:history:"
    SENTIMENT_RESULT = "sentiment:result:"
    EMBEDDING_CACHE = "embedding:cache:" 