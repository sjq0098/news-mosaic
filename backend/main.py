"""
News Mosaic - 多模态大模型新闻搜索分析工具

主应用入口文件
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from core.config import settings
from core.database import init_database, close_database
from core.cache import init_redis, close_redis
from api import news, chat, user, sentiment, news_card
from services.background_tasks import init_celery
from api.embedding import router as embedding_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动 News Mosaic 应用...")
    
    # 初始化数据库连接
    await init_database()
    logger.info("数据库连接已初始化")
    
    # 初始化 Redis 连接
    await init_redis()
    logger.info("Redis 连接已初始化")
    
    # 初始化 Celery 任务队列
    init_celery()
    logger.info("Celery 任务队列已初始化")
    
    yield
    
    # 关闭时清理资源
    logger.info("关闭 News Mosaic 应用...")
    await close_database()
    await close_redis()
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="News Mosaic API",
    description="多模态大模型新闻搜索分析工具 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置可信主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS.split(",")
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = logger.opt(record=True).info(f"请求开始: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = logger.opt(record=True).info(f"请求完成: {request.method} {request.url} - 状态码: {response.status_code}")
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "message": str(exc) if settings.DEBUG else "请联系管理员"
        }
    )


# 根路由
@app.get("/")
async def root():
    """根路由 - API 健康检查"""
    return {
        "message": "News Mosaic API",
        "version": "1.0.0",
        "status": "运行中",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "健康",
        "timestamp": logger.opt(record=True).info("健康检查")
    }


# 注册路由
app.include_router(news.router, prefix="/api/news", tags=["新闻"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["情感分析"])
app.include_router(embedding_router, prefix="/api/embedding", tags=["embedding"])
app.include_router(news_card.router, tags=["新闻卡片"])



# 导入并注册Pipeline API
from api.pipeline import router as pipeline_router
app.include_router(pipeline_router, tags=["智能分析Pipeline"])

# 导入并注册智能聊天API
from api.intelligent_chat import router as intelligent_chat_router
app.include_router(intelligent_chat_router, prefix="/api/v1/intelligent", tags=["智能助手"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )