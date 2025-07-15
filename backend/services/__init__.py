"""
服务模块
"""

from .qwen_service import qwen_service
from .news_service import news_service
from .chat_service import chat_service
#from .embedding_service import embedding_service

__all__ = [
    "qwen_service",
    "news_service", 
    "chat_service",
    #"embedding_service"
] 