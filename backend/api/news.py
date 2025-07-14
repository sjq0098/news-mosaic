"""
新闻 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime

from models.news import (
    NewsResponse, NewsCreate, NewsUpdate, NewsSearchQuery, 
    NewsSearchResponse, NewsStats, NewsCategory, NewsSource
)
from services.news_service import NewsService
from core.cache import cache, CacheKeys

router = APIRouter()

def get_news_service() -> NewsService:
    """获取新闻服务实例"""
    return NewsService()


@router.get("/search", response_model=NewsSearchResponse)
async def search_news(
    query: str = Query(..., description="搜索关键词"),
    category: Optional[NewsCategory] = Query(None, description="新闻分类"),
    source: Optional[NewsSource] = Query(None, description="新闻来源"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    sort_by: str = Query("published_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    news_service: NewsService = Depends(get_news_service)
):
    """搜索新闻"""
    
    # 构建搜索查询
    search_query = NewsSearchQuery(
        query=query,
        category=category,
        source=source,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 生成缓存键
    cache_key = f"{CacheKeys.NEWS_SEARCH}{hash(str(search_query))}"
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # 搜索新闻
    result = await news_service.search_news(search_query)
    
    # 缓存结果
    await cache.set(cache_key, result.dict(), expire=1800)  # 30分钟缓存
    
    return result


@router.get("/latest", response_model=List[NewsResponse])
async def get_latest_news(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    category: Optional[NewsCategory] = Query(None, description="新闻分类"),
    news_service: NewsService = Depends(get_news_service)
):
    """获取最新新闻"""
    
    cache_key = f"{CacheKeys.NEWS_SEARCH}latest:{category}:{limit}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    result = await news_service.get_latest_news(limit=limit, category=category)
    await cache.set(cache_key, [news.dict() for news in result], expire=600)  # 10分钟缓存
    
    return result


@router.get("/trending", response_model=List[NewsResponse])
async def get_trending_news(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    news_service: NewsService = Depends(get_news_service)
):
    """获取热门新闻"""
    
    cache_key = f"{CacheKeys.NEWS_SEARCH}trending:{hours}:{limit}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    result = await news_service.get_trending_news(limit=limit, hours=hours)
    await cache.set(cache_key, [news.dict() for news in result], expire=1800)  # 30分钟缓存
    
    return result


@router.get("/stats", response_model=NewsStats)
async def get_news_stats(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    news_service: NewsService = Depends(get_news_service)
):
    """获取新闻统计信息"""
    
    cache_key = f"{CacheKeys.NEWS_SEARCH}stats:{days}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    result = await news_service.get_news_stats(days=days)
    await cache.set(cache_key, result.dict(), expire=3600)  # 1小时缓存
    
    return result


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(
    news_id: str,
    news_service: NewsService = Depends(get_news_service)
):
    """获取新闻详情"""
    
    cache_key = f"{CacheKeys.NEWS_DETAIL}{news_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    news = await news_service.get_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    # 增加浏览量
    await news_service.increment_view_count(news_id)
    
    await cache.set(cache_key, news.dict(), expire=3600)  # 1小时缓存
    
    return news


@router.post("/", response_model=NewsResponse)
async def create_news(
    news_data: NewsCreate,
    news_service: NewsService = Depends(get_news_service)
):
    """创建新闻（管理员功能）"""
    
    result = await news_service.create_news(news_data)
    
    # 清除相关缓存
    await cache.flush_pattern(f"{CacheKeys.NEWS_SEARCH}*")
    
    return result


@router.put("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: str,
    news_data: NewsUpdate,
    news_service: NewsService = Depends(get_news_service)
):
    """更新新闻（管理员功能）"""
    
    result = await news_service.update_news(news_id, news_data)
    if not result:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    # 清除相关缓存
    await cache.delete(f"{CacheKeys.NEWS_DETAIL}{news_id}")
    await cache.flush_pattern(f"{CacheKeys.NEWS_SEARCH}*")
    
    return result


@router.delete("/{news_id}")
async def delete_news(
    news_id: str,
    news_service: NewsService = Depends(get_news_service)
):
    """删除新闻（管理员功能）"""
    
    success = await news_service.delete_news(news_id)
    if not success:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    # 清除相关缓存
    await cache.delete(f"{CacheKeys.NEWS_DETAIL}{news_id}")
    await cache.flush_pattern(f"{CacheKeys.NEWS_SEARCH}*")
    
    return {"message": "新闻删除成功"}


@router.post("/{news_id}/like")
async def like_news(
    news_id: str,
    news_service: NewsService = Depends(get_news_service)
):
    """点赞新闻"""
    
    success = await news_service.like_news(news_id)
    if not success:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    # 清除详情缓存
    await cache.delete(f"{CacheKeys.NEWS_DETAIL}{news_id}")
    
    return {"message": "点赞成功"}


@router.post("/{news_id}/share")
async def share_news(
    news_id: str,
    news_service: NewsService = Depends(get_news_service)
):
    """分享新闻"""
    
    success = await news_service.share_news(news_id)
    if not success:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    # 清除详情缓存
    await cache.delete(f"{CacheKeys.NEWS_DETAIL}{news_id}")
    
    return {"message": "分享成功"}


@router.post("/fetch")
async def fetch_news(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="获取数量"),
    source: Optional[NewsSource] = Query(None, description="指定新闻源"),
    news_service: NewsService = Depends(get_news_service)
):
    """手动触发新闻获取"""
    
    result = await news_service.fetch_news_from_api(
        query=query, 
        limit=limit, 
        source=source
    )
    
    # 清除搜索缓存
    await cache.flush_pattern(f"{CacheKeys.NEWS_SEARCH}*")
    
    return {
        "message": f"成功获取 {len(result)} 条新闻",
        "news_count": len(result)
    } 