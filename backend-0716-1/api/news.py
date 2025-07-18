"""
新闻搜索 API 路由
提供新闻搜索、刷新、统计等 HTTP 接口
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging

from models.news import (
    NewsSearchRequest, NewsSearchResult, NewsRefreshResult,
    NewsStatistics, NewsListResponse
)
from services.news_service import get_news_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=NewsSearchResult)
async def search_news(request: NewsSearchRequest):
    """
    搜索新闻并保存到数据库
    
    Args:
        request: 新闻搜索请求
        
    Returns:
        NewsSearchResult: 搜索结果
    """
    try:
        service = await get_news_service()
        result = await service.search_and_save_news(request)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索新闻失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.post("/refresh/{session_id}", response_model=NewsRefreshResult)
async def refresh_news(session_id: str, expire_days: int = 3):
    """
    刷新指定会话的过期新闻
    
    Args:
        session_id: 会话ID
        expire_days: 过期天数
        
    Returns:
        NewsRefreshResult: 刷新结果
    """
    try:
        service = await get_news_service()
        result = await service.refresh_expired_news(session_id, expire_days)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新新闻失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新失败: {str(e)}"
        )


@router.get("/statistics", response_model=NewsStatistics)
async def get_statistics(session_id: Optional[str] = None):
    """
    获取新闻统计信息
    
    Args:
        session_id: 会话ID（可选）
        
    Returns:
        NewsStatistics: 统计信息
    """
    try:
        service = await get_news_service()
        result = await service.get_news_statistics(session_id)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取统计信息失败"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/list/{session_id}", response_model=NewsListResponse)
async def get_news_list(session_id: str, limit: int = 20, offset: int = 0):
    """
    获取指定会话的新闻列表
    
    Args:
        session_id: 会话ID
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        NewsListResponse: 新闻列表
    """
    try:
        service = await get_news_service()
        result = await service.get_session_news_list(session_id, limit, offset)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取新闻列表失败"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取新闻列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取新闻列表失败: {str(e)}"
        )
