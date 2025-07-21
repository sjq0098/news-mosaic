"""
增强RAG对话 API
基于向量检索的智能新闻问答接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from loguru import logger

from core.auth import get_current_user
from services.enhanced_rag_chat_service import (
    EnhancedRAGChatService,
    RAGChatRequest,
    RAGChatResponse,
    get_enhanced_rag_chat_service
)

router = APIRouter(prefix="/api/enhanced-chat", tags=["增强RAG对话"])


@router.post("/chat", response_model=RAGChatResponse)
async def chat_with_rag(
    request: RAGChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    基于RAG的智能对话
    
    功能特性：
    1. 向量检索相关新闻
    2. 多轮对话上下文管理
    3. 用户记忆和个性化
    4. 智能回复生成
    5. 后续问题推荐
    
    Args:
        request: RAG对话请求
        current_user: 当前用户信息
        chat_service: RAG对话服务
        
    Returns:
        RAGChatResponse: 对话响应
    """
    try:
        # 设置用户ID
        request.user_id = current_user.get("user_id", "anonymous")
        
        logger.info(f"用户 {request.user_id} 开始RAG对话: {request.message[:50]}...")
        
        # 执行RAG对话
        response = await chat_service.chat_with_rag(request)
        
        logger.info(f"RAG对话完成: session={response.session_id}, 成功={response.success}")
        
        return response
        
    except Exception as e:
        logger.error(f"RAG对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话失败: {str(e)}"
        )


@router.post("/quick-chat")
async def quick_chat(
    message: str,
    session_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    快速对话 - 使用默认配置
    
    Args:
        message: 用户消息
        session_id: 会话ID（可选）
        current_user: 当前用户
        chat_service: 对话服务
        
    Returns:
        简化的对话响应
    """
    try:
        request = RAGChatRequest(
            user_id=current_user.get("user_id", "anonymous"),
            message=message,
            session_id=session_id,
            max_context_news=5,
            similarity_threshold=0.7,
            temperature=0.7,
            max_tokens=800,
            use_user_memory=True,
            include_related_news=True,
            enable_personalization=True
        )
        
        response = await chat_service.chat_with_rag(request)
        
        # 返回简化响应
        return {
            "success": response.success,
            "session_id": response.session_id,
            "ai_response": response.ai_response,
            "confidence_score": response.confidence_score,
            "sources_count": response.sources_count,
            "follow_up_questions": response.follow_up_questions[:3],
            "processing_time": response.processing_time
        }
        
    except Exception as e:
        logger.error(f"快速对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速对话失败: {str(e)}"
        )


@router.post("/news-qa")
async def news_question_answer(
    question: str,
    news_topic: Optional[str] = None,
    max_sources: int = 3,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    新闻问答 - 专门针对新闻内容的问答
    
    Args:
        question: 用户问题
        news_topic: 新闻主题（可选）
        max_sources: 最大新闻源数量
        current_user: 当前用户
        chat_service: 对话服务
    """
    try:
        # 如果指定了新闻主题，将其加入问题中
        enhanced_question = f"{news_topic} {question}" if news_topic else question
        
        request = RAGChatRequest(
            user_id=current_user.get("user_id", "anonymous"),
            message=enhanced_question,
            max_context_news=max_sources,
            similarity_threshold=0.6,  # 降低阈值以获取更多相关内容
            temperature=0.5,  # 降低温度以获得更准确的回答
            max_tokens=600,
            use_user_memory=False,  # 专注于新闻内容，不使用用户记忆
            include_related_news=True,
            enable_personalization=False
        )
        
        response = await chat_service.chat_with_rag(request)
        
        return {
            "success": response.success,
            "question": question,
            "answer": response.ai_response,
            "confidence": response.confidence_score,
            "sources": response.relevant_news,
            "context_summary": response.context_summary,
            "related_topics": response.related_topics
        }
        
    except Exception as e:
        logger.error(f"新闻问答失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新闻问答失败: {str(e)}"
        )


@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    获取对话历史
    
    Args:
        session_id: 会话ID
        limit: 消息数量限制
        current_user: 当前用户
        chat_service: 对话服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 获取对话上下文
        conversation = await chat_service._get_or_create_conversation(session_id, user_id)
        
        # 获取最近的消息
        recent_messages = conversation.messages[-limit:] if conversation.messages else []
        
        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "message_count": len(recent_messages),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "message_type": msg.message_type.value,
                    "metadata": getattr(msg, 'metadata', {})
                }
                for msg in recent_messages
            ],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
        
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    删除对话
    
    Args:
        session_id: 会话ID
        current_user: 当前用户
        chat_service: 对话服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 从数据库删除
        await chat_service.db[chat_service.db.Collections.CONVERSATIONS].delete_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        # 从缓存删除
        if session_id in chat_service.conversation_cache:
            del chat_service.conversation_cache[session_id]
        
        return {
            "success": True,
            "message": "对话已删除",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除对话失败: {str(e)}"
        )


@router.get("/user/conversations")
async def get_user_conversations(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: EnhancedRAGChatService = Depends(get_enhanced_rag_chat_service)
):
    """
    获取用户的所有对话列表
    
    Args:
        limit: 对话数量限制
        current_user: 当前用户
        chat_service: 对话服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 从数据库查询用户的对话
        conversations = await chat_service.db[chat_service.db.Collections.CONVERSATIONS].find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(limit).to_list(length=limit)
        
        conversation_list = []
        for conv in conversations:
            # 获取最后一条消息作为预览
            messages = conv.get("messages", [])
            last_message = messages[-1] if messages else None
            
            conversation_list.append({
                "session_id": conv["session_id"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "message_count": len(messages),
                "last_message": last_message.get("content", "") if last_message else "",
                "last_message_time": last_message.get("timestamp") if last_message else None
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "conversation_count": len(conversation_list),
            "conversations": conversation_list
        }
        
    except Exception as e:
        logger.error(f"获取用户对话列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户对话列表失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "enhanced-rag-chat",
        "version": "1.0.0",
        "features": [
            "vector_retrieval",
            "multi_turn_conversation",
            "user_memory",
            "personalization",
            "follow_up_questions",
            "confidence_scoring"
        ]
    }
