"""
聊天对话 API 路由 - 使用 QWEN 模型
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import time

from models.chat import (
    ChatResponse, ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate,
    ChatSession, ChatMessage, ChatHistory, MessageReaction
)
from services.chat_service import ChatService, get_chat_service
from services.qwen_service import QWENService, get_qwen_service
from core.cache import cache, CacheKeys

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessageCreate,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
    qwen_service: QWENService = Depends(get_qwen_service)
):
    """发送聊天消息并获取 QWEN 回复"""
    
    start_time = time.time()
    
    try:
        # 如果是新会话，创建会话
        session_id = message_data.session_id
        if not session_id:
            session = await chat_service.create_chat_session(
                ChatSessionCreate(title="新对话")
            )
            session_id = session.id
        
        # 发送消息并获取回复
        result = await chat_service.send_message(message_data)
        
        # 构建响应
        session = await chat_service.get_chat_session(session_id)
        messages = await chat_service.get_session_messages(session_id)
        
        response_time = time.time() - start_time
        
        return ChatResponse(
            session=session,
            messages=messages,
            response_time=response_time,
            tokens_used=result.get("tokens_used", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务错误: {str(e)}")


@router.post("/message", response_model=ChatResponse)
async def send_message_compat(
    message_data: ChatMessageCreate,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
    qwen_service: QWENService = Depends(get_qwen_service)
):
    """发送聊天消息并获取 QWEN 回复（兼容路由）"""
    start_time = time.time()
    
    try:
        # 发送消息并获取回复
        result = await chat_service.send_message(message_data)
        
        # 获取会话ID
        session_id = result["session"].id
        
        # 构建响应
        session = result["session"]
        messages = await chat_service.get_session_messages(session_id)
        
        response_time = time.time() - start_time
        
        return ChatResponse(
            session=session,
            messages=messages,
            response_time=response_time,
            tokens_used=result.get("tokens_used", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务错误: {str(e)}")


@router.get("/sessions", response_model=ChatHistory)
async def get_chat_sessions(
    page: int = 1,
    size: int = 20,
    user_id: Optional[str] = None,
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取聊天会话列表"""
    
    cache_key = f"{CacheKeys.CHAT_HISTORY}{user_id}:{page}:{size}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    result = await chat_service.get_chat_sessions(
        user_id=user_id,
        page=page,
        size=size
    )
    
    # 构建ChatHistory响应
    chat_history = ChatHistory(
        sessions=result["sessions"],
        total=result["total"],
        page=result["page"],
        size=result["size"]
    )
    
    await cache.set(cache_key, chat_history.dict(), expire=300)  # 5分钟缓存
    return chat_history


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取特定聊天会话"""
    
    session = await chat_service.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return session


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话消息列表"""
    
    cache_key = f"{CacheKeys.CHAT_HISTORY}messages:{session_id}:{limit}:{offset}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    messages = await chat_service.get_session_messages(
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    await cache.set(cache_key, [msg.dict() for msg in messages], expire=300)
    return messages


@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate,
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建新的聊天会话"""
    
    session = await chat_service.create_chat_session(session_data)
    
    # 清除会话列表缓存
    await cache.flush_pattern(f"{CacheKeys.CHAT_HISTORY}*")
    
    return session


@router.put("/sessions/{session_id}", response_model=ChatSession)
async def update_chat_session(
    session_id: str,
    session_data: ChatSessionUpdate,
    chat_service: ChatService = Depends(get_chat_service)
):
    """更新聊天会话"""
    
    session = await chat_service.update_chat_session(session_id, session_data)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 清除相关缓存
    await cache.flush_pattern(f"{CacheKeys.CHAT_HISTORY}*")
    
    return session


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """删除聊天会话"""
    
    success = await chat_service.delete_chat_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 清除相关缓存
    await cache.flush_pattern(f"{CacheKeys.CHAT_HISTORY}*")
    
    return {"message": "会话删除成功"}


@router.post("/messages/{message_id}/reaction")
async def add_message_reaction(
    message_id: str,
    reaction_type: str,
    user_id: Optional[str] = None,
    chat_service: ChatService = Depends(get_chat_service)
):
    """为消息添加反应（点赞/点踩等）"""
    
    reaction = await chat_service.add_message_reaction(
        message_id=message_id,
        reaction_type=reaction_type,
        user_id=user_id
    )
    
    return {"message": "反应添加成功", "reaction_id": reaction.message_id}


@router.post("/sessions/{session_id}/regenerate")
async def regenerate_last_response(
    session_id: str,
    temperature: float = 0.7,
    chat_service: ChatService = Depends(get_chat_service),
    qwen_service: QWENService = Depends(get_qwen_service)
):
    """重新生成最后一条AI回复"""
    
    # 获取最后一条用户消息
    messages = await chat_service.get_session_messages(session_id, limit=10)
    if not messages:
        raise HTTPException(status_code=400, detail="会话中没有消息")
    
    last_user_message = None
    for msg in reversed(messages):
        if msg.role == "user":
            last_user_message = msg
            break
    
    if not last_user_message:
        raise HTTPException(status_code=400, detail="没有找到用户消息")
    
    # 删除最后一条AI回复（如果存在）
    if messages[0].role == "assistant":
        await chat_service.delete_message(messages[0].id)
    
    # 重新生成回复
    chat_history = await chat_service.get_session_messages(session_id, limit=10)
    qwen_response = await qwen_service.generate_response(
        user_message=last_user_message.content,
        chat_history=chat_history,
        temperature=temperature
    )
    
    # 保存新的AI回复
    ai_message = await chat_service.add_message(
        session_id=session_id,
        role="assistant",
        content=qwen_response.content,
        model_name="qwen",
        tokens_used=qwen_response.tokens_used,
        generation_time=qwen_response.generation_time
    )
    
    # 清除相关缓存
    await cache.flush_pattern(f"{CacheKeys.CHAT_HISTORY}*")
    
    return {"message": "回复重新生成成功", "message_id": ai_message.id}


@router.get("/models/qwen/status")
async def get_qwen_model_status(
    qwen_service: QWENService = Depends(get_qwen_service)
):
    """获取 QWEN 模型状态"""
    
    status = await qwen_service.get_model_status()
    return status