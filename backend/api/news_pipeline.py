"""
新闻处理流水线 API
提供统一的新闻处理接口，整合搜索、存储、分析、卡片生成等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List
from loguru import logger

from core.auth import get_current_user
from services.news_processing_pipeline import (
    NewsProcessingPipeline,
    NewsProcessingRequest,
    NewsProcessingResponse,
    get_news_pipeline
)

router = APIRouter(prefix="/api/news-pipeline", tags=["新闻处理流水线"])


@router.post("/process", response_model=NewsProcessingResponse)
async def process_news_pipeline(
    request: NewsProcessingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: NewsProcessingPipeline = Depends(get_news_pipeline)
):
    """
    执行完整的新闻处理流水线
    
    整合以下功能：
    1. SerpAPI 新闻搜索
    2. MongoDB 数据存储
    3. 向量化处理
    4. 通义千问 AI 分析
    5. 新闻卡片生成
    6. 情感分析
    7. 用户记忆更新
    
    Args:
        request: 新闻处理请求
        current_user: 当前用户信息
        pipeline: 新闻处理流水线服务
        
    Returns:
        NewsProcessingResponse: 处理结果
    """
    try:
        # 设置用户ID
        request.user_id = current_user.get("user_id", "anonymous")
        
        logger.info(f"用户 {request.user_id} 开始新闻处理流水线: {request.query}")
        
        # 执行流水线
        response = await pipeline.process_news_pipeline(request)
        
        logger.info(f"新闻处理流水线完成: {response.pipeline_id}, 成功: {response.success}")
        
        return response
        
    except Exception as e:
        logger.error(f"新闻处理流水线执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新闻处理流水线执行失败: {str(e)}"
        )


@router.post("/quick-process")
async def quick_process_news(
    query: str,
    num_results: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: NewsProcessingPipeline = Depends(get_news_pipeline)
):
    """
    快速新闻处理 - 使用默认配置
    
    Args:
        query: 搜索查询
        num_results: 结果数量
        current_user: 当前用户
        pipeline: 流水线服务
        
    Returns:
        简化的处理结果
    """
    try:
        request = NewsProcessingRequest(
            query=query,
            user_id=current_user.get("user_id", "anonymous"),
            num_results=num_results,
            enable_storage=True,
            enable_vectorization=True,
            enable_ai_analysis=True,
            enable_card_generation=True,
            enable_sentiment_analysis=True,
            enable_user_memory=True,
            max_cards=5
        )
        
        response = await pipeline.process_news_pipeline(request)
        
        # 返回简化结果
        return {
            "success": response.success,
            "message": response.message,
            "query": response.query,
            "total_found": response.total_found,
            "cards_generated": response.cards_generated,
            "ai_summary": response.ai_summary,
            "sentiment_overview": response.sentiment_overview,
            "processing_time": response.processing_time,
            "news_cards": response.news_cards[:3],  # 只返回前3张卡片
            "recommended_queries": response.recommended_queries
        }
        
    except Exception as e:
        logger.error(f"快速新闻处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速新闻处理失败: {str(e)}"
        )


@router.post("/search-and-analyze")
async def search_and_analyze_news(
    query: str,
    enable_cards: bool = True,
    enable_sentiment: bool = True,
    max_results: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: NewsProcessingPipeline = Depends(get_news_pipeline)
):
    """
    搜索并分析新闻 - 专注于分析功能
    
    Args:
        query: 搜索查询
        enable_cards: 是否生成卡片
        enable_sentiment: 是否情感分析
        max_results: 最大结果数
        current_user: 当前用户
        pipeline: 流水线服务
    """
    try:
        request = NewsProcessingRequest(
            query=query,
            user_id=current_user.get("user_id", "anonymous"),
            num_results=max_results,
            enable_storage=False,  # 不存储，只分析
            enable_vectorization=False,
            enable_ai_analysis=True,
            enable_card_generation=enable_cards,
            enable_sentiment_analysis=enable_sentiment,
            enable_user_memory=True,
            max_cards=10
        )
        
        response = await pipeline.process_news_pipeline(request)
        
        return {
            "success": response.success,
            "query": response.query,
            "analysis": {
                "ai_summary": response.ai_summary,
                "sentiment_overview": response.sentiment_overview,
                "total_analyzed": response.total_found
            },
            "cards": response.news_cards if enable_cards else [],
            "processing_time": response.processing_time,
            "recommended_queries": response.recommended_queries
        }
        
    except Exception as e:
        logger.error(f"搜索分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索分析失败: {str(e)}"
        )


@router.post("/batch-process")
async def batch_process_news(
    queries: List[str],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: NewsProcessingPipeline = Depends(get_news_pipeline)
):
    """
    批量处理多个查询 - 后台任务
    
    Args:
        queries: 查询列表
        background_tasks: 后台任务
        current_user: 当前用户
        pipeline: 流水线服务
    """
    try:
        if len(queries) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="批量查询数量不能超过10个"
            )
        
        user_id = current_user.get("user_id", "anonymous")
        
        # 添加后台任务
        for query in queries:
            background_tasks.add_task(
                _process_single_query,
                pipeline,
                query,
                user_id
            )
        
        return {
            "success": True,
            "message": f"已提交 {len(queries)} 个查询进行后台处理",
            "queries": queries,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量处理失败: {str(e)}"
        )


async def _process_single_query(pipeline: NewsProcessingPipeline, query: str, user_id: str):
    """处理单个查询的后台任务"""
    try:
        request = NewsProcessingRequest(
            query=query,
            user_id=user_id,
            num_results=15,
            enable_storage=True,
            enable_vectorization=True,
            enable_ai_analysis=True,
            enable_card_generation=True,
            enable_sentiment_analysis=True,
            enable_user_memory=True,
            max_cards=5
        )
        
        response = await pipeline.process_news_pipeline(request)
        logger.info(f"后台处理完成: {query}, 成功: {response.success}")
        
    except Exception as e:
        logger.error(f"后台处理失败 {query}: {e}")


@router.get("/status/{pipeline_id}")
async def get_pipeline_status(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取流水线处理状态
    
    Args:
        pipeline_id: 流水线ID
        current_user: 当前用户
    """
    # 这里可以实现状态查询逻辑
    # 实际项目中可能需要Redis或数据库来存储状态
    return {
        "pipeline_id": pipeline_id,
        "status": "completed",
        "message": "流水线处理完成"
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "news-processing-pipeline",
        "version": "1.0.0",
        "features": [
            "news_search",
            "data_storage",
            "vectorization",
            "ai_analysis",
            "card_generation",
            "sentiment_analysis",
            "user_memory"
        ]
    }
