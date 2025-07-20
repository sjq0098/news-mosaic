"""
Pipeline API - 提供完整的新闻智能分析Pipeline接口

整合增强对话、RAG、Embedding和卡片生成功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import json
import logging

from services.complete_pipeline_service import (
    CompletePipelineService, 
    PipelineRequest, 
    PipelineResponse,
    PipelineMode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["智能分析Pipeline"])

# 全局服务实例
pipeline_service = CompletePipelineService()

# 简化的请求模型（用于常见场景）
class SimplePipelineRequest(BaseModel):
    """简化的Pipeline请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID，不提供会自动生成")
    
class QuickChatRequest(BaseModel):
    """快速对话请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    user_id: str = Field(..., description="用户ID")
    enable_memory: bool = Field(default=True, description="启用记忆功能")

class NewsAnalysisRequest(BaseModel):
    """新闻分析请求"""
    query: str = Field(..., description="分析查询", min_length=1, max_length=500)
    user_id: str = Field(..., description="用户ID")
    max_results: int = Field(default=5, description="最大结果数", ge=1, le=20)
    generate_cards: bool = Field(default=True, description="生成新闻卡片")

class CustomPipelineRequest(BaseModel):
    """自定义Pipeline请求"""
    message: str = Field(..., description="用户消息")
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    # 功能开关
    enable_chat: bool = Field(default=True, description="启用智能对话")
    enable_rag: bool = Field(default=True, description="启用新闻检索")
    enable_cards: bool = Field(default=True, description="启用卡片生成")
    enable_memory: bool = Field(default=True, description="启用用户记忆")
    
    # 参数设置
    max_news: int = Field(default=5, description="最大新闻数量", ge=1, le=20)
    max_cards: int = Field(default=3, description="最大卡片数量", ge=1, le=10)
    similarity_threshold: float = Field(default=0.7, description="相似度阈值", ge=0.0, le=1.0)

# 响应模型
class PipelineStatusResponse(BaseModel):
    """Pipeline状态响应"""
    status: str
    services: Dict[str, str]
    modes: List[str]
    timestamp: str

class QuickChatResponse(BaseModel):
    """快速对话响应"""
    response: str
    session_id: str
    personalized: bool
    confidence: float
    suggested_questions: List[str]
    execution_time: float

class NewsAnalysisResponse(BaseModel):
    """新闻分析响应"""
    summary: str
    news_count: int
    cards_count: int
    news_articles: List[Dict[str, Any]]
    news_cards: List[Dict[str, Any]]
    analysis_time: float
    quality_score: float

# API端点
@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """
    获取Pipeline状态
    
    Returns:
        Pipeline服务状态和可用功能
    """
    try:
        status = await pipeline_service.get_pipeline_status()
        return PipelineStatusResponse(**status)
    except Exception as e:
        logger.error(f"获取Pipeline状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务状态检查失败: {str(e)}")

@router.post("/complete", response_model=PipelineResponse)
async def process_complete_pipeline(request: PipelineRequest):
    """
    完整Pipeline处理
    
    提供最全面的功能，包括增强对话、RAG检索、卡片生成和记忆管理
    
    Args:
        request: 完整的Pipeline请求参数
        
    Returns:
        完整的Pipeline处理结果
    """
    try:
        logger.info(f"处理完整Pipeline请求: user_id={request.user_id}, mode={request.mode}")
        
        response = await pipeline_service.process_pipeline(request)
        
        logger.info(f"Pipeline处理完成: success={response.success}, time={response.total_execution_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"完整Pipeline处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline处理失败: {str(e)}")

@router.post("/simple", response_model=PipelineResponse)
async def process_simple_pipeline(request: SimplePipelineRequest):
    """
    简化Pipeline处理
    
    使用默认设置进行完整处理，适合大多数使用场景
    
    Args:
        request: 简化的Pipeline请求
        
    Returns:
        完整的Pipeline处理结果
    """
    try:
        # 转换为完整请求
        full_request = PipelineRequest(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            mode=PipelineMode.UNIFIED_COMPLETE
        )
        
        response = await pipeline_service.process_pipeline(full_request)
        return response
        
    except Exception as e:
        logger.error(f"简化Pipeline处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"简化Pipeline处理失败: {str(e)}")

@router.post("/chat", response_model=QuickChatResponse)
async def quick_chat(request: QuickChatRequest):
    """
    快速智能对话
    
    仅使用增强对话功能，不进行新闻检索和卡片生成
    
    Args:
        request: 快速对话请求
        
    Returns:
        对话响应结果
    """
    try:
        # 构建Pipeline请求
        pipeline_request = PipelineRequest(
            user_id=request.user_id,
            message=request.message,
            mode=PipelineMode.ENHANCED_CHAT,
            enable_memory=request.enable_memory,
            enable_rag=False,
            enable_cards=False
        )
        
        response = await pipeline_service.process_pipeline(pipeline_request)
        
        return QuickChatResponse(
            response=response.ai_response,
            session_id=response.session_id,
            personalized=response.enhanced_chat.result.get("personalized", False) if response.enhanced_chat.result else False,
            confidence=response.confidence_score,
            suggested_questions=response.suggested_questions,
            execution_time=response.total_execution_time
        )
        
    except Exception as e:
        logger.error(f"快速对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")

@router.post("/news", response_model=NewsAnalysisResponse)
async def analyze_news(request: NewsAnalysisRequest):
    """
    新闻智能分析
    
    专注于新闻检索和分析，可选择生成新闻卡片
    
    Args:
        request: 新闻分析请求
        
    Returns:
        新闻分析结果
    """
    try:
        # 构建Pipeline请求
        mode = PipelineMode.CARD_GENERATION if request.generate_cards else PipelineMode.RAG_ANALYSIS
        
        pipeline_request = PipelineRequest(
            user_id=request.user_id,
            message=request.query,
            mode=mode,
            enable_rag=True,
            enable_cards=request.generate_cards,
            enable_memory=False,
            max_results=request.max_results,
            card_count=3 if request.generate_cards else 0
        )
        
        response = await pipeline_service.process_pipeline(pipeline_request)
        
        return NewsAnalysisResponse(
            summary=response.ai_response,
            news_count=len(response.retrieved_news),
            cards_count=len(response.generated_cards),
            news_articles=response.retrieved_news,
            news_cards=response.generated_cards,
            analysis_time=response.total_execution_time,
            quality_score=response.confidence_score
        )
        
    except Exception as e:
        logger.error(f"新闻分析处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"新闻分析失败: {str(e)}")

@router.post("/custom", response_model=PipelineResponse)
async def custom_pipeline(request: CustomPipelineRequest):
    """
    自定义Pipeline处理
    
    根据用户指定的功能开关进行定制化处理
    
    Args:
        request: 自定义Pipeline请求
        
    Returns:
        定制化处理结果
    """
    try:
        # 构建Pipeline请求
        pipeline_request = PipelineRequest(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            mode=PipelineMode.CUSTOM,
            enable_memory=request.enable_memory,
            enable_rag=request.enable_rag,
            enable_cards=request.enable_cards,
            enable_personalization=request.enable_chat,
            max_results=request.max_news,
            card_count=request.max_cards,
            similarity_threshold=request.similarity_threshold
        )
        
        response = await pipeline_service.process_pipeline(pipeline_request)
        return response
        
    except Exception as e:
        logger.error(f"自定义Pipeline处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"自定义处理失败: {str(e)}")

@router.post("/stream/chat")
async def stream_chat(request: QuickChatRequest):
    """
    流式对话响应
    
    提供实时的流式对话体验
    
    Args:
        request: 快速对话请求
        
    Returns:
        Server-Sent Events流式响应
    """
    async def generate_stream():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始处理您的请求...'})}\n\n"
            
            # 构建并处理请求
            pipeline_request = PipelineRequest(
                user_id=request.user_id,
                message=request.message,
                mode=PipelineMode.ENHANCED_CHAT,
                enable_memory=request.enable_memory,
                enable_rag=False,
                enable_cards=False
            )
            
            response = await pipeline_service.process_pipeline(pipeline_request)
            
            # 分块发送响应
            response_text = response.ai_response
            chunk_size = 20  # 每次发送的字符数
            
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
                await asyncio.sleep(0.1)  # 模拟打字效果
            
            # 发送完成信号
            final_data = {
                'type': 'complete',
                'session_id': response.session_id,
                'confidence': response.confidence_score,
                'suggested_questions': response.suggested_questions,
                'execution_time': response.total_execution_time
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f'处理失败: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/modes")
async def get_pipeline_modes():
    """
    获取可用的Pipeline处理模式
    
    Returns:
        可用模式列表和说明
    """
    modes = {
        PipelineMode.ENHANCED_CHAT: {
            "name": "增强对话",
            "description": "智能对话，支持记忆和个性化",
            "features": ["memory", "personalization", "context"]
        },
        PipelineMode.RAG_ANALYSIS: {
            "name": "新闻检索分析", 
            "description": "基于RAG的新闻智能检索和分析",
            "features": ["news_search", "semantic_analysis", "relevance_ranking"]
        },
        PipelineMode.CARD_GENERATION: {
            "name": "新闻卡片生成",
            "description": "生成结构化的新闻分析卡片",
            "features": ["news_cards", "structured_analysis", "visual_summary"]
        },
        PipelineMode.UNIFIED_COMPLETE: {
            "name": "完整统一处理",
            "description": "集成所有功能的完整处理流程",
            "features": ["all_features", "best_experience", "comprehensive_analysis"]
        },
        PipelineMode.CUSTOM: {
            "name": "自定义处理",
            "description": "根据用户需求定制功能组合",
            "features": ["flexible", "customizable", "selective_features"]
        }
    }
    
    return {
        "modes": modes,
        "default": PipelineMode.UNIFIED_COMPLETE,
        "recommended": {
            "chat": PipelineMode.ENHANCED_CHAT,
            "news": PipelineMode.RAG_ANALYSIS,
            "analysis": PipelineMode.UNIFIED_COMPLETE
        }
    }

@router.get("/health")
async def pipeline_health_check():
    """
    Pipeline健康检查
    
    Returns:
        服务健康状态
    """
    try:
        status = await pipeline_service.get_pipeline_status()
        
        # 检查关键服务
        critical_services = ["unified_service", "enhanced_chat", "rag_service"]
        healthy = all(status["services"].get(service) == "就绪" for service in critical_services)
        
        return {
            "status": "healthy" if healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": status["services"],
            "uptime": "运行正常"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# 批量处理端点
@router.post("/batch")
async def batch_process(
    requests: List[SimplePipelineRequest],
    max_concurrent: int = Query(default=5, description="最大并发数", ge=1, le=10)
):
    """
    批量处理Pipeline请求
    
    Args:
        requests: 批量请求列表
        max_concurrent: 最大并发处理数
        
    Returns:
        批量处理结果
    """
    if len(requests) > 20:
        raise HTTPException(status_code=400, detail="批量请求数量不能超过20个")
    
    try:
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(req: SimplePipelineRequest):
            async with semaphore:
                pipeline_request = PipelineRequest(
                    user_id=req.user_id,
                    session_id=req.session_id,
                    message=req.message,
                    mode=PipelineMode.UNIFIED_COMPLETE
                )
                return await pipeline_service.process_pipeline(pipeline_request)
        
        # 并行处理所有请求
        start_time = datetime.now()
        results = await asyncio.gather(*[process_single(req) for req in requests], return_exceptions=True)
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 处理结果
        success_count = sum(1 for r in results if isinstance(r, PipelineResponse) and r.success)
        error_count = len(results) - success_count
        
        return {
            "total_requests": len(requests),
            "success_count": success_count,
            "error_count": error_count,
            "total_time": total_time,
            "average_time": total_time / len(requests),
            "results": [
                r if isinstance(r, PipelineResponse) else {"error": str(r)}
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")