"""
智能聊天 API 路由 - 智能体交互接口
提供与智能新闻助手的对话功能
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime

from models.agent import ChatMessage, ChatResponse
from services.news_agent_service import get_news_agent_service, get_available_models, get_default_model

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
        
        # 获取用户指定的模型名称（如果有），否则为None
        model_name = getattr(chat_data, 'model_name', None)
        # 异步获取对应模型的智能体服务实例
        agent_service = await get_news_agent_service(model_name)
        
        # 调用智能体服务处理用户消息，返回结果
        result = await agent_service.process_user_message(
            user_id=chat_data.user_id,
            session_id=chat_data.session_id,
            message=chat_data.message
        )
        
        # 构建聊天响应对象，包含智能体回复、类型、关键词、搜索结果和使用的模型
        response = ChatResponse(
            success=True,
            data={
                "reply": result.get("reply", "抱歉，我遇到了一些问题。"),
                "type": result.get("type", "unknown"),
                "keywords_used": result.get("keywords_used", []),
                "search_result": result.get("search_result"),
                "model_used": agent_service.model_name
            }
        )
        
        logger.info(f"聊天响应成功 [用户: {chat_data.user_id}, 模型: {agent_service.model_name}]")
        return response
        
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        return ChatResponse(
            success=False,
            error=f"聊天处理失败: {str(e)}"
        )


@router.get("/health")
async def chat_health_check():
    """
    检查聊天服务健康状态
    Returns:
        Dict: 服务状态信息
    """
    try:
        # 异步检查智能体服务是否可用
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


@router.get("/models")
async def get_models():
    """
    获取可用的AI模型列表
    Returns:
        Dict: 模型信息
    """
    try:
        available_models = get_available_models()
        default_model = get_default_model()
        
        return {
            "success": True,
            "data": {
                "available_models": available_models,
                "default_model": default_model,
                "total_count": len(available_models)
            }
        }
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return {
            "success": False,
            "error": f"获取模型列表失败: {str(e)}"
        }


@router.post("/models/test")
async def test_model(model_data: Dict[str, Any]):
    """
    测试指定模型的可用性
    Args:
        model_data: 包含model_name的字典
    Returns:
        Dict: 测试结果
    """
    try:
        model_name = model_data.get("model_name")
        if not model_name:
            return {
                "success": False,
                "error": "缺少model_name参数"
            }
        
        available_models = get_available_models()
        if model_name not in available_models:
            return {
                "success": False,
                "error": f"模型 {model_name} 不在可用列表中",
                "available_models": available_models
            }
        
        agent_service = await get_news_agent_service(model_name)
        
        # 使用测试用户和会话，发送简单消息进行模型测试
        test_result = await agent_service.process_user_message(
            user_id="test_user",
            session_id="test_session",
            message="你好"
        )
        
        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "status": "available",
                "test_response": test_result.get("reply", "")[:100] + "..." if len(test_result.get("reply", "")) > 100 else test_result.get("reply", ""),
                "response_type": test_result.get("type", "unknown")
            }
        }
        
    except Exception as e:
        logger.error(f"测试模型失败: {str(e)}")
        return {
            "success": False,
            "error": f"测试模型失败: {str(e)}"
        }