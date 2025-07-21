"""
统一新闻处理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from loguru import logger

from core.auth import get_current_user
from services.unified_news_service import (
    UnifiedNewsService,
    UnifiedNewsRequest,
    UnifiedNewsResponse
)

router = APIRouter(prefix="/api/unified-news", tags=["统一新闻处理"])


@router.post("/process", response_model=UnifiedNewsResponse)
async def process_news_unified(
    request: UnifiedNewsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    统一新闻处理接口
    
    整合以下功能：
    1. SerpAPI 新闻搜索
    2. MongoDB 数据存储
    3. 通义千问 AI 分析
    4. 新闻卡片生成
    
    Args:
        request: 统一新闻处理请求
        current_user: 当前用户信息
        service: 统一新闻服务
    
    Returns:
        UnifiedNewsResponse: 处理结果
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求统一新闻处理: {request.query}")

        # 设置用户ID
        request.user_id = current_user["id"]

        # 创建服务实例并处理新闻
        service = UnifiedNewsService()
        response = await service.process_news_unified(request)
        
        if response.success:
            logger.info(f"统一新闻处理成功: 找到 {response.total_found} 条新闻，生成 {response.cards_generated} 张卡片")
        else:
            logger.warning(f"统一新闻处理失败: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"统一新闻处理异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


@router.post("/quick-search", response_model=UnifiedNewsResponse)
async def quick_news_search(
    query: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    快速新闻搜索（使用默认参数）
    
    Args:
        query: 搜索查询
        current_user: 当前用户信息
        service: 统一新闻服务
    
    Returns:
        UnifiedNewsResponse: 处理结果
    """
    try:
        logger.info(f"用户 {current_user['username']} 快速搜索: {query}")
        
        # 创建默认请求
        request = UnifiedNewsRequest(
            query=query,
            user_id=current_user["id"],
            num_results=10,
            enable_storage=True,
            enable_analysis=True,
            enable_cards=True,
            max_cards=3
        )
        
        # 创建服务实例并处理新闻
        service = UnifiedNewsService()
        response = await service.process_news_unified(request)
        
        return response
        
    except Exception as e:
        logger.error(f"快速新闻搜索异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.post("/search-and-analyze", response_model=UnifiedNewsResponse)
async def search_and_analyze_news(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    搜索并分析新闻（灵活参数）
    
    Args:
        request: 包含搜索参数的字典
        current_user: 当前用户信息
        service: 统一新闻服务
    
    Returns:
        UnifiedNewsResponse: 处理结果
    """
    try:
        # 提取必需参数
        query = request.get("query")
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少搜索查询参数"
            )
        
        logger.info(f"用户 {current_user['username']} 搜索分析: {query}")
        
        # 构建请求
        unified_request = UnifiedNewsRequest(
            query=query,
            user_id=current_user["id"],
            num_results=request.get("num_results", 10),
            language=request.get("language", "zh-cn"),
            country=request.get("country", "cn"),
            time_period=request.get("time_period", "1d"),
            enable_storage=request.get("enable_storage", True),
            enable_analysis=request.get("enable_analysis", True),
            enable_cards=request.get("enable_cards", True),
            max_cards=request.get("max_cards", 5),
            include_sentiment=request.get("include_sentiment", True),
            include_summary=request.get("include_summary", True)
        )
        
        # 创建服务实例并处理新闻
        service = UnifiedNewsService()
        response = await service.process_news_unified(unified_request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索分析新闻异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "unified-news",
        "message": "统一新闻处理服务运行正常"
    }
