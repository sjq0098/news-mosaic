"""
情感分析 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional

from models.sentiment import (
    SentimentResponse, SentimentAnalysisRequest, BatchSentimentRequest,
    BatchSentimentResponse, SentimentStats, SentimentTrend
)
from services.sentiment_service import SentimentService
from core.cache import cache, CacheKeys

router = APIRouter()

def get_sentiment_service() -> SentimentService:
    """获取情感分析服务实例"""
    return SentimentService()


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    background_tasks: BackgroundTasks,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """单文本情感分析"""
    
    try:
        # 生成缓存键（基于文本内容）
        cache_key = f"{CacheKeys.SENTIMENT_RESULT}{hash(request.text)}"
        
        # 尝试从缓存获取结果
        cached_result = await cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 执行情感分析
        result = await sentiment_service.analyze_sentiment(request)
        
        # 缓存结果
        await cache.set(cache_key, result.dict(), expire=3600)  # 1小时缓存
        
        # 异步保存分析结果到数据库
        if request.news_id or request.user_id:
            background_tasks.add_task(
                sentiment_service.save_analysis_result,
                result.analysis
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"情感分析失败: {str(e)}"
        )


@router.post("/batch-analyze", response_model=BatchSentimentResponse)
async def batch_analyze_sentiment(
    request: BatchSentimentRequest,
    background_tasks: BackgroundTasks,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """批量文本情感分析"""
    
    try:
        # 检查文本数量限制
        if len(request.texts) > 100:
            raise HTTPException(
                status_code=400,
                detail="批量分析文本数量不能超过100条"
            )
        
        # 执行批量情感分析
        result = await sentiment_service.batch_analyze_sentiment(request)
        
        # 异步缓存单个分析结果
        background_tasks.add_task(
            sentiment_service.cache_batch_results,
            request.texts,
            result.results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量情感分析失败: {str(e)}"
        )


@router.get("/news/{news_id}", response_model=SentimentResponse)
async def get_news_sentiment(
    news_id: str,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """获取新闻的情感分析结果"""
    
    cache_key = f"{CacheKeys.SENTIMENT_RESULT}news:{news_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    result = await sentiment_service.get_news_sentiment(news_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="未找到该新闻的情感分析结果"
        )
    
    await cache.set(cache_key, result.dict(), expire=3600)
    return result


@router.post("/news/{news_id}/analyze", response_model=SentimentResponse)
async def analyze_news_sentiment(
    news_id: str,
    background_tasks: BackgroundTasks,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """分析指定新闻的情感"""
    
    try:
        result = await sentiment_service.analyze_news_sentiment(news_id)
        
        # 异步保存结果
        background_tasks.add_task(
            sentiment_service.save_analysis_result,
            result.analysis
        )
        
        # 清除相关缓存
        await cache.delete(f"{CacheKeys.SENTIMENT_RESULT}news:{news_id}")
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"新闻情感分析失败: {str(e)}"
        )


@router.get("/stats", response_model=SentimentStats)
async def get_sentiment_stats(
    days: int = 7,
    category: Optional[str] = None,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """获取情感分析统计信息"""
    
    cache_key = f"{CacheKeys.SENTIMENT_RESULT}stats:{days}:{category}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    stats = await sentiment_service.get_sentiment_stats(
        days=days,
        category=category
    )
    
    await cache.set(cache_key, stats.dict(), expire=1800)  # 30分钟缓存
    return stats


@router.get("/trends", response_model=List[SentimentTrend])
async def get_sentiment_trends(
    days: int = 30,
    category: Optional[str] = None,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """获取情感趋势数据"""
    
    cache_key = f"{CacheKeys.SENTIMENT_RESULT}trends:{days}:{category}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    trends = await sentiment_service.get_sentiment_trends(
        days=days,
        category=category
    )
    
    await cache.set(cache_key, [trend.dict() for trend in trends], expire=3600)
    return trends


@router.get("/models")
async def get_available_models(
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """获取可用的情感分析模型列表"""
    
    models = await sentiment_service.get_available_models()
    return {"models": models}


@router.get("/models/{model_name}/performance")
async def get_model_performance(
    model_name: str,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """获取模型性能指标"""
    
    cache_key = f"{CacheKeys.SENTIMENT_RESULT}performance:{model_name}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    performance = await sentiment_service.get_model_performance(model_name)
    await cache.set(cache_key, performance, expire=7200)  # 2小时缓存
    
    return performance


@router.post("/feedback")
async def submit_sentiment_feedback(
    analysis_id: str,
    correct_label: str,
    feedback_text: Optional[str] = None,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """提交情感分析反馈（用于模型改进）"""
    
    try:
        success = await sentiment_service.submit_feedback(
            analysis_id=analysis_id,
            correct_label=correct_label,
            feedback_text=feedback_text
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="分析结果不存在"
            )
        
        return {"message": "反馈提交成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"反馈提交失败: {str(e)}"
        )


@router.delete("/analysis/{analysis_id}")
async def delete_sentiment_analysis(
    analysis_id: str,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """删除情感分析结果"""
    
    try:
        success = await sentiment_service.delete_analysis(analysis_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="分析结果不存在"
            )
        
        # 清除相关缓存
        await cache.flush_pattern(f"{CacheKeys.SENTIMENT_RESULT}*")
        
        return {"message": "分析结果删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/retrain")
async def retrain_sentiment_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    sentiment_service: SentimentService = Depends(get_sentiment_service)
):
    """重新训练情感分析模型（管理员功能）"""
    
    try:
        # 启动后台重训练任务
        background_tasks.add_task(
            sentiment_service.retrain_model,
            model_name
        )
        
        return {"message": f"模型 {model_name} 重训练任务已启动"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"重训练启动失败: {str(e)}"
        ) 