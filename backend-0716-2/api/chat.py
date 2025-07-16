"""
智能对话 API 路由
基于智能体服务的自然语言交互接口
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from models.chat import ChatRequest, ChatResponse
from services.news_agent_service import get_news_agent_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    处理用户对话消息
    
    Args:
        request: 对话请求
        
    Returns:
        ChatResponse: 对话响应
    """
    try:
        # 获取智能体服务
        agent_service = await get_news_agent_service()
        
        # 处理用户消息
        result = await agent_service.process_user_message(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message
        )
        
        return ChatResponse(
            message_id=f"msg_{int(request.timestamp.timestamp())}",
            reply=result.get("reply", "抱歉，处理出现问题"),
            reply_type=result.get("type", "error"),
            keywords_extracted=result.get("keywords_used", []),
            news_found=result.get("news_count", 0),
            success=True,
            timestamp=request.timestamp
        )
        
    except Exception as e:
        logger.error(f"处理对话消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理消息失败: {str(e)}"
        )


@router.post("/intro")
async def get_intro_message(user_id: str, session_id: str):
    """
    获取欢迎介绍消息
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        
    Returns:
        Dict: 介绍消息
    """
    try:
        agent_service = await get_news_agent_service()
        
        intro_result = await agent_service.get_intro_message(
            user_id=user_id,
            session_id=session_id
        )
        
        return {
            "success": True,
            "message": intro_result.get("reply", ""),
            "type": "intro"
        }
        
    except Exception as e:
        logger.error(f"获取介绍消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取介绍消息失败: {str(e)}"
        )


@router.get("/health")
async def check_agent_health():
    """
    检查智能体服务健康状态
    
    Returns:
        Dict: 健康状态
    """
    try:
        agent_service = await get_news_agent_service()
        
        # 简单的健康检查
        test_result = await agent_service.health_check()
        
        return {
            "status": "healthy" if test_result else "unhealthy",
            "service": "news_agent",
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"智能体健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "news_agent", 
            "error": str(e),
            "timestamp": str(datetime.now())
        }
