"""
聊天对话 API 路由 - 智能体交互接口
提供与智能新闻助手的对话功能
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
import uuid
from datetime import datetime

from models.agent import ChatMessage, ChatResponse
from services.news_agent_service import get_news_agent_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_data: ChatMessage):
    """
    与智能体进行对话
    
    Args:
        chat_data: 聊天消息数据
        
    Returns:
        ChatResponse: 智能体响应
    """
    try:
        logger.info(f"收到聊天请求 [用户: {chat_data.user_id}, 会话: {chat_data.session_id}]")
        
        # 获取智能体服务
        agent_service = await get_news_agent_service()
        
        # 处理用户消息
        result = await agent_service.process_user_message(
            user_id=chat_data.user_id,
            session_id=chat_data.session_id,
            message=chat_data.message
        )
        
        # 构建响应
        response = ChatResponse(
            success=True,
            data={
                "reply": result.get("reply", "抱歉，我遇到了一些问题。"),
                "type": result.get("type", "unknown"),
                "keywords_used": result.get("keywords_used", []),
                "search_result": result.get("search_result")
            }
        )
        
        logger.info(f"聊天响应成功 [用户: {chat_data.user_id}]")
        return response
        
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        return ChatResponse(
            success=False,
            error=f"聊天处理失败: {str(e)}"
        )


@router.get("/chat/health")
async def chat_health_check():
    """
    检查聊天服务健康状态
    
    Returns:
        Dict: 服务状态信息
    """
    try:
        # 检查智能体服务是否可用
        agent_service = await get_news_agent_service()
        
        return {
            "status": "healthy",
            "service": "chat_api",
            "timestamp": datetime.now().isoformat(),
            "agent_service": "available"
        }
        
    except Exception as e:
        logger.error(f"聊天服务健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"聊天服务不可用: {str(e)}"
        )
