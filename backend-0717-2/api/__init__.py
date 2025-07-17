"""
API 包
"""

try:
    from .user import router as user_router
    from .news import router as news_router
    from .chat import router as chat_router
    __all__ = ["user_router", "news_router", "chat_router"]
except ImportError:
    # 如果 fastapi 未安装，则不导入
    __all__ = []
