"""
后台任务服务 - Celery 任务队列管理
"""

from celery import Celery
from loguru import logger

from core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "news_mosaic",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "services.tasks.news_tasks",
        "services.tasks.sentiment_tasks",
        "services.tasks.vector_tasks"
    ]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    "fetch-news-periodically": {
        "task": "services.tasks.news_tasks.fetch_news_task",
        "schedule": settings.NEWS_FETCH_INTERVAL,  # 5分钟执行一次
        "args": (["科技", "AI", "人工智能"], 20)
    },
    "cleanup-old-news": {
        "task": "services.tasks.news_tasks.cleanup_old_news_task",
        "schedule": settings.NEWS_CLEANUP_INTERVAL,  # 24小时执行一次
        "args": (30,)  # 清理30天前的新闻
    },
    "update-sentiment-stats": {
        "task": "services.tasks.sentiment_tasks.update_sentiment_stats_task",
        "schedule": 3600.0,  # 1小时执行一次
    },
    "refresh-vector-index": {
        "task": "services.tasks.vector_tasks.refresh_vector_index_task",
        "schedule": 7200.0,  # 2小时执行一次
    }
}

celery_app.conf.timezone = "Asia/Shanghai"


def init_celery():
    """初始化 Celery"""
    logger.info("Celery 任务队列初始化完成")
    return celery_app


# 导出 Celery 应用
__all__ = ["celery_app", "init_celery"] 