"""
缓存管理模块 - 简单内存缓存实现
用于缓存用户兴趣、会话信息等频繁访问的数据
"""

import time
import asyncio
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """简单的内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300) -> None:
        """
        初始化缓存
        
        Args:
            default_ttl: 默认过期时间（秒）
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """定期清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理任务异常: {e}")
    
    async def _cleanup_expired(self):
        """清理过期的缓存项"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self._cache.items():
            if current_time > item['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        if time.time() > item['expires_at']:
            del self._cache[key]
            return None
        
        item['access_count'] += 1
        item['last_access'] = time.time()
        return item['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用default_ttl
        """
        ttl = ttl or self.default_ttl
        current_time = time.time()
        
        self._cache[key] = {
            'value': value,
            'expires_at': current_time + ttl,
            'created_at': current_time,
            'last_access': current_time,
            'access_count': 0
        }
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        total_items = len(self._cache)
        expired_items = sum(1 for item in self._cache.values() 
                          if current_time > item['expires_at'])
        
        return {
            'total_items': total_items,
            'active_items': total_items - expired_items,
            'expired_items': expired_items,
            'cache_keys': list(self._cache.keys())
        }
    
    def stop_cleanup_task(self):
        """停止清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# 全局缓存实例
_global_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = SimpleCache()
    return _global_cache


async def cache_user_interests(user_id: str, interests: list, ttl: int = 600) -> None:
    """缓存用户兴趣列表"""
    cache = get_cache()
    await cache.set(f"user_interests:{user_id}", interests, ttl)


async def get_cached_user_interests(user_id: str) -> Optional[list]:
    """获取缓存的用户兴趣列表"""
    cache = get_cache()
    return await cache.get(f"user_interests:{user_id}")


async def invalidate_user_cache(user_id: str) -> None:
    """清除用户相关的所有缓存"""
    cache = get_cache()
    await cache.delete(f"user_interests:{user_id}")
    await cache.delete(f"user_sessions:{user_id}")
    logger.debug(f"已清除用户 {user_id} 的缓存")
