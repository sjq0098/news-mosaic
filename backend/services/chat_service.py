"""
聊天服务模块
"""
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from models.chat import (
    ChatSession, ChatMessage, ChatMessageCreate, ChatSessionCreate, 
    ChatSessionUpdate, MessageRole, MessageType, ChatStatus, MessageReaction
)
from .qwen_service import QWENService
from core.cache import cache, CacheKeys

logger = logging.getLogger(__name__)


@dataclass
class ChatServiceConfig:
    """聊天服务配置"""
    max_sessions_per_user: int = 50
    max_messages_per_session: int = 1000
    session_ttl: int = 86400 * 7  # 7天
    auto_title_threshold: int = 3  # 当消息数量达到3条时自动生成标题


class ChatService:
    """聊天服务"""
    
    def __init__(self):
        self.config = ChatServiceConfig()
        self.qwen_service = QWENService()
        # 临时存储（实际应用中应该使用数据库）
        self._sessions: Dict[str, ChatSession] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._reactions: Dict[str, List[MessageReaction]] = {}
    
    async def send_message(
        self,
        message_data: ChatMessageCreate,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """发送消息并获取AI回复"""
        start_time = datetime.now()
        
        try:
            # 获取或创建会话
            session = await self._get_or_create_session(
                message_data.session_id, 
                user_id
            )
            
            # 创建用户消息
            user_message = await self._create_message(
                session_id=session.id,
                role=MessageRole.USER,
                content=message_data.content,
                message_type=message_data.message_type,
                user_id=user_id
            )
            
            # 获取聊天历史
            chat_history = await self.get_session_messages(session.id, limit=10)
            
            # 生成AI回复
            ai_response = await self.qwen_service.generate_response(
                user_message=message_data.content,
                chat_history=chat_history,
                include_news=message_data.include_news,
                news_limit=message_data.news_limit,
                temperature=message_data.temperature,
                max_tokens=message_data.max_tokens
            )
            
            # 创建AI回复消息
            ai_message = await self._create_message(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=ai_response.content,
                message_type=MessageType.TEXT,
                llm_model=message_data.llm_model or "qwen",
                tokens_used=ai_response.tokens_used,
                generation_time=ai_response.generation_time,
                news_ids=ai_response.news_ids
            )
            
            # 更新会话
            await self._update_session_after_message(session, ai_message)
            
            # 自动生成标题
            if session.message_count == self.config.auto_title_threshold:
                await self._auto_generate_title(session)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "session": session,
                "user_message": user_message,
                "ai_message": ai_message,
                "response_time": processing_time,
                "tokens_used": ai_response.tokens_used
            }
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """获取会话消息"""
        messages = self._messages.get(session_id, [])
        return messages[offset:offset + limit]
    
    async def get_chat_sessions(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """获取聊天会话列表"""
        # 过滤用户的会话
        sessions = []
        for session in self._sessions.values():
            if user_id is None or session.user_id == user_id:
                sessions.append(session)
        
        # 按最后消息时间排序
        sessions.sort(key=lambda x: x.last_message_at or x.created_at, reverse=True)
        
        # 分页
        start = (page - 1) * size
        end = start + size
        page_sessions = sessions[start:end]
        
        return {
            "sessions": page_sessions,
            "total": len(sessions),
            "page": page,
            "size": size
        }
    
    async def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """获取单个聊天会话"""
        return self._sessions.get(session_id)
    
    async def create_chat_session(
        self,
        session_data: ChatSessionCreate,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """创建新的聊天会话"""
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=session_data.title or "新对话",
            settings=session_data.settings or {},
            status=ChatStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._sessions[session_id] = session
        self._messages[session_id] = []
        
        return session
    
    async def update_chat_session(
        self,
        session_id: str,
        session_data: ChatSessionUpdate
    ) -> Optional[ChatSession]:
        """更新聊天会话"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # 更新字段
        if session_data.title is not None:
            session.title = session_data.title
        if session_data.is_pinned is not None:
            session.is_pinned = session_data.is_pinned
        if session_data.status is not None:
            session.status = session_data.status
        if session_data.settings is not None:
            session.settings = session_data.settings
        
        session.updated_at = datetime.now()
        
        return session
    
    async def delete_chat_session(self, session_id: str) -> bool:
        """删除聊天会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if session_id in self._messages:
                del self._messages[session_id]
            if session_id in self._reactions:
                del self._reactions[session_id]
            return True
        return False
    
    async def add_message_reaction(
        self,
        message_id: str,
        reaction_type: str,
        user_id: Optional[str] = None
    ) -> MessageReaction:
        """添加消息反应"""
        reaction = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            reaction_type=reaction_type,
            created_at=datetime.now()
        )
        
        if message_id not in self._reactions:
            self._reactions[message_id] = []
        
        self._reactions[message_id].append(reaction)
        
        return reaction
    
    async def regenerate_last_response(
        self,
        session_id: str,
        temperature: float = 0.7
    ) -> Optional[ChatMessage]:
        """重新生成最后一条AI回复"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        messages = self._messages.get(session_id, [])
        if len(messages) < 2:
            return None
        
        # 获取最后一条用户消息
        last_user_message = None
        for message in reversed(messages):
            if message.role == MessageRole.USER:
                last_user_message = message
                break
        
        if not last_user_message:
            return None
        
        # 移除最后一条AI回复
        if messages and messages[-1].role == MessageRole.ASSISTANT:
            messages.pop()
            session.message_count -= 1
        
        # 生成新回复
        ai_response = await self.qwen_service.generate_response(
            user_message=last_user_message.content,
            chat_history=messages[:-1],  # 排除当前用户消息
            temperature=temperature
        )
        
        # 创建新的AI消息
        ai_message = await self._create_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            message_type=MessageType.TEXT,
            llm_model="qwen",
            tokens_used=ai_response.tokens_used,
            generation_time=ai_response.generation_time
        )
        
        return ai_message
    
    async def _get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: Optional[str]
    ) -> ChatSession:
        """获取或创建会话"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        
        # 创建新会话
        session_data = ChatSessionCreate(title="新对话")
        return await self.create_chat_session(session_data, user_id)
    
    async def _create_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        user_id: Optional[str] = None,
        llm_model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        generation_time: Optional[float] = None,
        news_ids: Optional[List[str]] = None
    ) -> ChatMessage:
        """创建消息"""
        message_id = str(uuid.uuid4())
        
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            llm_model=llm_model,
            tokens_used=tokens_used,
            generation_time=generation_time,
            news_ids=news_ids or [],
            created_at=datetime.now()
        )
        
        if session_id not in self._messages:
            self._messages[session_id] = []
        
        self._messages[session_id].append(message)
        
        return message
    
    async def _update_session_after_message(
        self,
        session: ChatSession,
        message: ChatMessage
    ):
        """消息后更新会话"""
        session.message_count += 1
        session.last_message_at = message.created_at
        session.updated_at = datetime.now()
        
        if message.tokens_used:
            session.total_tokens += message.tokens_used
    
    async def _auto_generate_title(self, session: ChatSession):
        """自动生成会话标题"""
        try:
            messages = self._messages.get(session.id, [])
            if len(messages) >= 2:
                # 使用前几条消息生成标题
                context = " ".join([
                    msg.content for msg in messages[:4]
                    if msg.role == MessageRole.USER
                ])
                
                # 这里可以调用AI服务生成标题，暂时简化处理
                if len(context) > 50:
                    session.title = context[:47] + "..."
                else:
                    session.title = context or "新对话"
                    
        except Exception as e:
            logger.warning(f"自动生成标题失败: {str(e)}")


# 全局实例
chat_service = ChatService()


async def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    return chat_service 