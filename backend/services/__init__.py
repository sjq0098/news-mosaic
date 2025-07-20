"""
服务模块
"""

from .qwen_service import qwen_service
from .news_service import news_service
from .chat_service import chat_service
from .news_agent_service import get_news_agent_service, NewsAgentService, get_available_models, get_default_model
from .user_interest_service import (
    add_user_interests,
    remove_user_interests,
    get_user_interests,
    clear_user_interests,
    query_related_interests,
    get_user_interest_service
)
from .memory_mongo import SessionMemoryStore
from .sentiment_service import SentimentService
#from .embedding_service import embedding_service

__all__ = [
    "qwen_service",
    "news_service", 
    "chat_service",
    "get_news_agent_service",
    "NewsAgentService", 
    "get_available_models",
    "get_default_model",
    "add_user_interests",
    "remove_user_interests",
    "get_user_interests", 
    "clear_user_interests",
    "query_related_interests",
    "get_user_interest_service",
    "SessionMemoryStore",
    "SentimentService",
    #"embedding_service"
]