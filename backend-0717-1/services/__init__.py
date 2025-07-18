"""
服务层包
"""

from .auth_service import get_user_auth_service, UserAuthService
from .news_service import get_news_service, NewsService

__all__ = [
    "get_user_auth_service",
    "UserAuthService",
    "get_news_service", 
    "NewsService"
]
