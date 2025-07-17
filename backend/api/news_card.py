"""
新闻结构化卡片API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from typing import List, Optional
from loguru import logger

from services.news_card_service import NewsCardService
from models.news_card import (
    NewsCardRequest, NewsCardResponse, 
    BatchNewsCardRequest, BatchNewsCardResponse,
    NewsCardStats, NewsCard
)


router = APIRouter(prefix="/api/v1/news-cards", tags=["新闻卡片"])


def get_news_card_service() -> NewsCardService:
    """获取新闻卡片服务实例"""
    return NewsCardService()


@router.post("/generate", response_model=NewsCardResponse)
async def generate_news_card(
    request: NewsCardRequest,
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    生成单个新闻结构化卡片
    
    Args:
        request: 新闻卡片生成请求
        
    Returns:
        NewsCardResponse: 生成的新闻卡片响应
        
    Raises:
        HTTPException: 400 - 请求参数错误
        HTTPException: 404 - 新闻不存在
        HTTPException: 500 - 服务器内部错误
    """
    try:
        logger.info(f"开始生成新闻卡片: {request.news_id}")
        response = await service.generate_card(request)
        logger.info(f"新闻卡片生成成功: {request.news_id}")
        return response
        
    except ValueError as e:
        logger.error(f"请求参数错误: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"生成新闻卡片失败: {e}")
        raise HTTPException(status_code=500, detail="生成新闻卡片失败")


@router.post("/generate/batch", response_model=BatchNewsCardResponse)
async def generate_batch_news_cards(
    request: BatchNewsCardRequest,
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    批量生成新闻结构化卡片
    
    Args:
        request: 批量新闻卡片生成请求
        
    Returns:
        BatchNewsCardResponse: 批量生成的新闻卡片响应
        
    Raises:
        HTTPException: 400 - 请求参数错误
        HTTPException: 500 - 服务器内部错误
    """
    try:
        if len(request.news_ids) == 0:
            raise HTTPException(status_code=400, detail="新闻ID列表不能为空")
        
        if len(request.news_ids) > 50:
            raise HTTPException(status_code=400, detail="一次最多处理50条新闻")
        
        logger.info(f"开始批量生成新闻卡片: {len(request.news_ids)}条")
        response = await service.generate_batch_cards(request)
        logger.info(f"批量生成完成: 成功{response.success_count}, 失败{response.failed_count}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量生成新闻卡片失败: {e}")
        raise HTTPException(status_code=500, detail="批量生成新闻卡片失败")


@router.post("/generate/background")
async def generate_news_card_background(
    request: NewsCardRequest,
    background_tasks: BackgroundTasks,
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    后台异步生成新闻结构化卡片
    
    Args:
        request: 新闻卡片生成请求
        background_tasks: FastAPI后台任务
        
    Returns:
        dict: 任务状态响应
    """
    async def generate_task():
        try:
            await service.generate_card(request)
            logger.info(f"后台生成新闻卡片完成: {request.news_id}")
        except Exception as e:
            logger.error(f"后台生成新闻卡片失败: {request.news_id}, 错误: {e}")
    
    background_tasks.add_task(generate_task)
    
    return {
        "message": "新闻卡片生成任务已提交到后台队列",
        "news_id": request.news_id,
        "status": "queued"
    }


@router.post("/generate/batch/background")
async def generate_batch_news_cards_background(
    request: BatchNewsCardRequest,
    background_tasks: BackgroundTasks,
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    后台异步批量生成新闻结构化卡片
    
    Args:
        request: 批量新闻卡片生成请求
        background_tasks: FastAPI后台任务
        
    Returns:
        dict: 任务状态响应
    """
    if len(request.news_ids) == 0:
        raise HTTPException(status_code=400, detail="新闻ID列表不能为空")
    
    if len(request.news_ids) > 100:
        raise HTTPException(status_code=400, detail="后台任务一次最多处理100条新闻")
    
    async def generate_batch_task():
        try:
            response = await service.generate_batch_cards(request)
            logger.info(f"后台批量生成完成: 成功{response.success_count}, 失败{response.failed_count}")
        except Exception as e:
            logger.error(f"后台批量生成失败: {e}")
    
    background_tasks.add_task(generate_batch_task)
    
    return {
        "message": "批量新闻卡片生成任务已提交到后台队列",
        "total_count": len(request.news_ids),
        "status": "queued"
    }


@router.get("/quick-generate/{news_id}", response_model=NewsCardResponse)
async def quick_generate_news_card(
    news_id: str,
    include_sentiment: bool = Query(default=True, description="是否包含情感分析"),
    include_entities: bool = Query(default=True, description="是否包含实体识别"),
    include_related: bool = Query(default=False, description="是否查找相关新闻"),
    max_summary_length: int = Query(default=200, ge=50, le=500, description="摘要最大长度"),
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    快速生成新闻卡片（使用默认参数）
    
    Args:
        news_id: 新闻ID
        include_sentiment: 是否包含情感分析
        include_entities: 是否包含实体识别
        include_related: 是否查找相关新闻
        max_summary_length: 摘要最大长度
        
    Returns:
        NewsCardResponse: 生成的新闻卡片响应
    """
    request = NewsCardRequest(
        news_id=news_id,
        include_sentiment=include_sentiment,
        include_entities=include_entities,
        include_related=include_related,
        max_summary_length=max_summary_length
    )
    
    return await generate_news_card(request, service)


@router.get("/templates")
async def get_card_templates():
    """
    获取新闻卡片模板配置
    
    Returns:
        dict: 卡片模板配置信息
    """
    return {
        "templates": {
            "basic": {
                "name": "基础卡片",
                "description": "包含标题、摘要、情感分析",
                "include_sentiment": True,
                "include_entities": False,
                "include_related": False,
                "max_summary_length": 200
            },
            "standard": {
                "name": "标准卡片",
                "description": "包含完整分析但不含相关新闻",
                "include_sentiment": True,
                "include_entities": True,
                "include_related": False,
                "max_summary_length": 300
            },
            "comprehensive": {
                "name": "完整卡片",
                "description": "包含所有分析功能",
                "include_sentiment": True,
                "include_entities": True,
                "include_related": True,
                "max_summary_length": 400
            },
            "fast": {
                "name": "快速卡片",
                "description": "仅基础信息，生成速度最快",
                "include_sentiment": False,
                "include_entities": False,
                "include_related": False,
                "max_summary_length": 150
            }
        },
        "importance_levels": {
            "critical": {"min_score": 9.0, "color": "#ff4444", "priority": 1},
            "high": {"min_score": 7.0, "color": "#ff8800", "priority": 2},
            "medium": {"min_score": 5.0, "color": "#ffbb00", "priority": 3},
            "low": {"min_score": 3.0, "color": "#88cc00", "priority": 4},
            "minimal": {"min_score": 0.0, "color": "#cccccc", "priority": 5}
        },
        "sentiment_colors": {
            "positive": "#4caf50",
            "negative": "#f44336",
            "neutral": "#9e9e9e",
            "mixed": "#ff9800"
        }
    }


@router.post("/templates/{template_name}/generate/{news_id}", response_model=NewsCardResponse)
async def generate_with_template(
    news_id: str,
    template_name: str,
    service: NewsCardService = Depends(get_news_card_service)
):
    """
    使用指定模板生成新闻卡片
    
    Args:
        news_id: 新闻ID
        template_name: 模板名称 (basic/standard/comprehensive/fast)
        
    Returns:
        NewsCardResponse: 生成的新闻卡片响应
    """
    templates = {
        "basic": {
            "include_sentiment": True,
            "include_entities": False,
            "include_related": False,
            "max_summary_length": 200
        },
        "standard": {
            "include_sentiment": True,
            "include_entities": True,
            "include_related": False,
            "max_summary_length": 300
        },
        "comprehensive": {
            "include_sentiment": True,
            "include_entities": True,
            "include_related": True,
            "max_summary_length": 400
        },
        "fast": {
            "include_sentiment": False,
            "include_entities": False,
            "include_related": False,
            "max_summary_length": 150
        }
    }
    
    if template_name not in templates:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的模板: {template_name}, 可用模板: {list(templates.keys())}"
        )
    
    template_config = templates[template_name]
    request = NewsCardRequest(
        news_id=news_id,
        **template_config
    )
    
    return await generate_news_card(request, service)


@router.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务状态信息
    """
    try:
        # 这里可以添加服务依赖检查
        return {
            "status": "healthy",
            "service": "news-card-service",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不可用")


# 这里可以添加更多的API端点，如：
# - 获取已生成的卡片
# - 更新卡片
# - 删除卡片
# - 卡片统计信息
# - 卡片搜索和筛选 