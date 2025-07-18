"""
数据模型包
"""

from .user import (
    UserCreateRequest,
    UserLoginRequest,
    UserSessionRequest,
    UserDeleteRequest,
    UserCreateResult,
    UserLoginResult,
    UserSessionResult,
    UserDeleteResponse,
    SessionDeleteResponse,
    UserSessionsResponse,
    UserPreferences,
    UserDocument,
    UserSessionDocument
)

from .news import (
    NewsSearchRequest,
    NewsSearchResult,
    NewsRefreshResult,
    NewsDocument,
    NewsStatistics,
    NewsListResponse
)

from .agent import (
    AgentState,
    AgentResponse,
    ChatMessage,
    ChatResponse
)

from .chat import (
    ChatHistoryItem,
    SessionMemory,
    ChatMemoryDocument
)

__all__ = [
    # 用户相关模型
    "UserCreateRequest",
    "UserLoginRequest", 
    "UserSessionRequest",
    "UserDeleteRequest",
    "UserCreateResult",
    "UserLoginResult",
    "UserSessionResult",
    "UserDeleteResponse",
    "SessionDeleteResponse", 
    "UserSessionsResponse",
    "UserPreferences",
    "UserDocument", 
    "UserSessionDocument",
    
    # 新闻相关模型
    "NewsSearchRequest",
    "NewsSearchResult",
    "NewsRefreshResult", 
    "NewsDocument",
    "NewsStatistics",
    "NewsListResponse",
    
    # 智能体相关模型
    "AgentState",
    "AgentResponse", 
    "ChatMessage",
    "ChatResponse",
    
    # 聊天相关模型
    "ChatHistoryItem",
    "SessionMemory",
    "ChatMemoryDocument"
]
