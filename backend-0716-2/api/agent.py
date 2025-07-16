"""
智能体API路由
提供智能新闻助手的HTTP接口
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from services.news_agent_service import get_news_agent_service
from services.agent_memory_service import get_agent_memory_service

router = APIRouter()
logger = logging.getLogger(__name__)


class AgentChatRequest(BaseModel):
    """智能体聊天请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., min_length=1, description="用户消息")


class AgentChatResponse(BaseModel):
    """智能体聊天响应模型"""
    reply: str = Field(..., description="智能体回复")
    thread_id: str = Field(..., description="线程ID")
    question_type: str = Field(..., description="问题类型")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具")
    keywords_used: Optional[List[str]] = Field(None, description="使用的关键词")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    status: str = Field(default="success", description="状态")


class AgentMemoryResponse(BaseModel):
    """智能体记忆响应模型"""
    thread_id: str = Field(..., description="线程ID")
    context: str = Field(..., description="对话上下文")
    status: str = Field(default="success", description="状态")


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    智能体聊天接口
    
    Args:
        request: 聊天请求
        
    Returns:
        AgentChatResponse: 聊天响应
    """
    try:
        logger.info(f"智能体聊天请求 [用户: {request.user_id}, 会话: {request.session_id}]: {request.message}")
        
        # 1. 获取服务实例
        agent_service = await get_news_agent_service()
        memory_service = await get_agent_memory_service()
        
        # 2. 获取或创建线程ID
        thread_id = await memory_service.get_or_create_thread_id(request.user_id, request.session_id)
        
        # 3. 获取对话上下文
        context = await memory_service.get_conversation_context(thread_id)
        
        # 4. 处理用户消息（加入上下文）
        enhanced_message = request.message
        if context:
            enhanced_message = f"对话历史:\n{context}\n\n当前用户问题: {request.message}"
        
        # 5. 调用智能体处理
        result = await agent_service.process_user_message(
            request.user_id, 
            request.session_id, 
            enhanced_message
        )
        
        # 6. 保存对话记录
        await memory_service.save_conversation_turn(
            thread_id=thread_id,
            user_message=request.message,
            agent_response=result["reply"],
            metadata={
                "question_type": result.get("type"),
                "tools_used": result.get("tools_used", []),
                "keywords_used": result.get("keywords_used")
            }
        )
        
        # 7. 构建响应
        response = AgentChatResponse(
            reply=result["reply"],
            thread_id=thread_id,
            question_type=result.get("type", "unknown"),
            tools_used=result.get("tools_used", []),
            keywords_used=result.get("keywords_used"),
            timestamp=datetime.now(),
            status="success" if result.get("type") != "error" else "error"
        )
        
        logger.info(f"智能体聊天完成 [线程: {thread_id}], 类型: {response.question_type}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"智能体聊天失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能体处理失败: {str(e)}"
        )


@router.get("/memory/{thread_id}", response_model=AgentMemoryResponse)
async def get_agent_memory(thread_id: str, max_turns: int = 10):
    """
    获取智能体记忆
    
    Args:
        thread_id: 线程ID
        max_turns: 最大轮数
        
    Returns:
        AgentMemoryResponse: 记忆响应
    """
    try:
        memory_service = await get_agent_memory_service()
        
        context = await memory_service.get_conversation_context(thread_id, max_turns)
        
        return AgentMemoryResponse(
            thread_id=thread_id,
            context=context,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"获取智能体记忆失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取记忆失败: {str(e)}"
        )


@router.delete("/memory/{thread_id}")
async def clear_agent_memory(thread_id: str):
    """
    清理智能体记忆
    
    Args:
        thread_id: 线程ID
        
    Returns:
        Dict: 清理结果
    """
    try:
        memory_service = await get_agent_memory_service()
        
        success = await memory_service.clear_thread_memory(thread_id)
        
        if success:
            return {
                "status": "success",
                "message": f"线程 {thread_id} 的记忆已清理",
                "thread_id": thread_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="记忆清理失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理智能体记忆失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理记忆失败: {str(e)}"
        )


@router.post("/memory/cleanup")
async def cleanup_expired_memories(expire_hours: int = 24):
    """
    清理过期记忆（管理员接口）
    
    Args:
        expire_hours: 过期小时数
        
    Returns:
        Dict: 清理结果
    """
    try:
        memory_service = await get_agent_memory_service()
        
        deleted_count = await memory_service.cleanup_expired_memories(expire_hours)
        
        return {
            "status": "success",
            "message": f"清理完成，删除 {deleted_count} 条过期记录",
            "deleted_count": deleted_count,
            "expire_hours": expire_hours
        }
        
    except Exception as e:
        logger.error(f"清理过期记忆失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}"
        )


@router.get("/health")
async def agent_health_check():
    """
    智能体健康检查
    
    Returns:
        Dict: 健康状态
    """
    try:
        # 检查服务可用性
        agent_service = await get_news_agent_service()
        memory_service = await get_agent_memory_service()
        
        return {
            "status": "healthy",
            "message": "智能体服务运行正常",
            "timestamp": datetime.now(),
            "services": {
                "agent_service": "available",
                "memory_service": "available"
            }
        }
        
    except Exception as e:
        logger.error(f"智能体健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"服务异常: {str(e)}",
            "timestamp": datetime.now()
        }
