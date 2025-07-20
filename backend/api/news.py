"""
新闻相关的 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from services.news_service import get_news_service, NewsService, NewsSearchResult

logger = logging.getLogger(__name__)

# 移除这里的 prefix，因为在 main.py 中已经设置了
router = APIRouter(tags=["新闻"])


class NewsSearchRequest(BaseModel):
    """新闻搜索请求模型"""
    query: str
    num_results: Optional[int] = 10
    language: Optional[str] = "zh-cn"
    country: Optional[str] = "cn"
    time_period: Optional[str] = "1d"


class NewsResponse(BaseModel):
    """新闻响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None


@router.get("/search", response_model=NewsResponse)
async def search_news(
    query: str = Query(..., description="搜索关键词"),
    num_results: int = Query(10, ge=1, le=50, description="返回结果数量"),
    language: str = Query("zh-cn", description="语言代码"),
    country: str = Query("cn", description="国家代码"),
    time_period: str = Query("1d", description="时间范围（1d, 1w, 1m, 1y）"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    搜索新闻
    
    - **query**: 搜索关键词
    - **num_results**: 返回结果数量（1-50）
    - **language**: 语言代码（zh-cn, en-us等）
    - **country**: 国家代码（cn, us等）
    - **time_period**: 时间范围（1d=1天, 1w=1周, 1m=1月, 1y=1年）
    """
    try:
        result = await news_service.search_news(
            query=query,
            num_results=num_results,
            language=language,
            country=country,
            time_period=time_period
        )
        
        return NewsResponse(
            success=True,
            message="新闻搜索成功",
            data=result.dict()
        )
        
    except Exception as e:
        logger.error(f"新闻搜索失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"新闻搜索失败: {str(e)}"
        )


@router.post("/search", response_model=NewsResponse)
async def search_news_post(
    request: NewsSearchRequest,
    news_service: NewsService = Depends(get_news_service)
):
    """
    搜索新闻（POST方式）
    """
    try:
        result = await news_service.search_news(
            query=request.query,
            num_results=request.num_results,
            language=request.language,
            country=request.country,
            time_period=request.time_period
        )
        
        return NewsResponse(
            success=True,
            message="新闻搜索成功",
            data=result.dict()
        )
        
    except Exception as e:
        logger.error(f"新闻搜索失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"新闻搜索失败: {str(e)}"
        )


@router.get("/trending", response_model=NewsResponse)
async def get_trending_news(
    language: str = Query("zh-cn", description="语言代码"),
    country: str = Query("cn", description="国家代码"),
    num_results: int = Query(20, ge=1, le=50, description="返回结果数量"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    获取热门新闻
    """
    try:
        result = await news_service.search_trending_news(
            language=language,
            country=country,
            num_results=num_results
        )
        
        return NewsResponse(
            success=True,
            message="获取热门新闻成功",
            data=result.dict()
        )
        
    except Exception as e:
        logger.error(f"获取热门新闻失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取热门新闻失败: {str(e)}"
        )


@router.get("/category/{category}", response_model=NewsResponse)
async def search_news_by_category(
    category: str,
    num_results: int = Query(10, ge=1, le=50, description="返回结果数量"),
    language: str = Query("zh-cn", description="语言代码"),
    country: str = Query("cn", description="国家代码"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    按分类搜索新闻
    
    支持的分类: 科技、体育、财经、娱乐、政治、健康、教育、国际
    """
    try:
        result = await news_service.search_news_by_category(
            category=category,
            num_results=num_results,
            language=language,
            country=country
        )
        
        return NewsResponse(
            success=True,
            message=f"获取{category}新闻成功",
            data=result.dict()
        )
        
    except Exception as e:
        logger.error(f"获取分类新闻失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取分类新闻失败: {str(e)}"
        )


@router.get("/sentiment", response_model=NewsResponse)
async def search_news_with_sentiment(
    query: str = Query(..., description="搜索关键词"),
    num_results: int = Query(10, ge=1, le=30, description="返回结果数量"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    搜索新闻并进行情感分析
    """
    try:
        result = await news_service.search_news_with_sentiment(
            query=query,
            num_results=num_results
        )
        
        return NewsResponse(
            success=True,
            message="新闻情感分析成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"新闻情感分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"新闻情感分析失败: {str(e)}"
        )


@router.get("/summary", response_model=NewsResponse)
async def get_news_summary(
    query: str = Query(..., description="搜索关键词"),
    num_articles: int = Query(5, ge=1, le=20, description="分析文章数量"),
    news_service: NewsService = Depends(get_news_service)
):
    """
    获取新闻摘要
    """
    try:
        result = await news_service.get_news_summary(
            query=query,
            num_articles=num_articles
        )
        
        return NewsResponse(
            success=True,
            message="获取新闻摘要成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取新闻摘要失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取新闻摘要失败: {str(e)}"
        )


@router.get("/categories", response_model=NewsResponse)
async def get_news_categories():
    """
    获取支持的新闻分类
    """
    categories = [
        {"key": "科技", "name": "科技", "description": "科技、人工智能、互联网等"},
        {"key": "体育", "name": "体育", "description": "体育运动、赛事、健身等"},
        {"key": "财经", "name": "财经", "description": "经济、股市、金融、投资等"},
        {"key": "娱乐", "name": "娱乐", "description": "明星、电影、音乐、游戏等"},
        {"key": "政治", "name": "政治", "description": "政府、政策、政治新闻等"},
        {"key": "健康", "name": "健康", "description": "医疗、养生、健康知识等"},
        {"key": "教育", "name": "教育", "description": "教育、学校、培训等"},
        {"key": "国际", "name": "国际", "description": "国际新闻、全球事件等"}
    ]
    
    return NewsResponse(
        success=True,
        message="获取新闻分类成功",
        data={"categories": categories}
    )