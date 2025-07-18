"""
News Mosaic Backend - 用户认证服务

主应用入口文件，提供用户注册、登录、会话管理等功能的 HTTP API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging

from core.config import settings
from core.database import init_database, close_database
from api.user import router as user_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动 News Mosaic 用户认证服务...")
    
    # 初始化数据库连接
    await init_database()
    logger.info("数据库连接已初始化")
    
    yield
    
    # 关闭时清理资源
    logger.info("关闭 News Mosaic 用户认证服务...")
    await close_database()
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="News Mosaic User Auth API",
    description="News Mosaic 用户认证服务 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    logger.info(f"请求开始: {request.method} {request.url}")
    
    response = await call_next(request)
    
    logger.info(f"请求完成: {request.method} {request.url} - 状态码: {response.status_code}")
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "message": str(exc)
        }
    )


# 根路由
@app.get("/")
async def root():
    """根路由 - API 健康检查"""
    return {
        "message": "News Mosaic User Auth API",
        "version": "1.0.0",
        "status": "运行中",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "健康",
        "service": "用户认证服务"
    }


# 注册路由
app.include_router(user_router, prefix="/api/v1/users", tags=["用户管理"])

try:
    from api.news import router as news_router
    app.include_router(news_router, prefix="/api/v1/news", tags=["新闻管理"])
except ImportError:
    logger.warning("新闻路由未加载，可能缺少依赖")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
