"""
应用配置管理模块 - 新闻搜索专用版
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = Field(default="news-mosaic-search", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=True, description="调试模式")
    
    # 新闻搜索 API 配置
    SERPAPI_KEY: str = Field(default="", description="SerpAPI 密钥")
    
    # LLM API 配置
    DASHSCOPE_API_KEY: str = Field(default="", description="通义千问API密钥")
    
    # 新闻配置
    DEFAULT_EXPIRE_DAYS: int = Field(default=3, description="新闻默认过期天数")
    MAX_SEARCH_RESULTS: int = Field(default=50, description="最大搜索结果数量")
    
    # 数据库配置
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", description="MongoDB 连接URL")
    MONGODB_DB_NAME: str = Field(default="news_mosaic", description="MongoDB 数据库名")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件")
    
    class Config:
        # 明确指定 .env 文件路径
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的字段


# 创建全局配置实例
settings = Settings()

# 为了兼容性，也提供一个 Config 别名
Config = settings