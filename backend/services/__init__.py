"""
业务服务层 - 处理核心业务逻辑
"""

from .qwen_service import qwen_service
from .news_service import news_service, get_news_service
from .chat_service import chat_service, get_chat_service
from .background_tasks import *

__version__ = "1.0.0" 