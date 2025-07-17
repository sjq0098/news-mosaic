"""
数据模型包
"""

from .user import (
    UserCreateRequest, UserLoginRequest, UserSessionRequest, UserDeleteRequest,
    UserCreateResult, UserLoginResult, UserSessionResult,
    UserDeleteResponse, SessionDeleteResponse, UserSessionsResponse
)

from .news import (
    NewsSearchRequest, NewsSearchResult, NewsRefreshResult, NewsDocument,
    NewsStatistics, NewsListResponse
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
    
    # 新闻相关模型
    "NewsSearchRequest",
    "NewsSearchResult",
    "NewsRefreshResult", 
    "NewsDocument",
    "NewsStatistics",
    "NewsListResponse"
]
