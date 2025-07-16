"""
应用配置管理模块 - 新闻搜索专用版
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = Field(default="news-mosaic-search", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=True, description="调试模式")
    
    # 新闻搜索 API 配置
    SERPAPI_KEY: str = Field(default="", description="SerpAPI 密钥")
    
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
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的字段


# 创建全局配置实例
settings = Settings()

# 调试：打印配置文件路径和密钥状态
config_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
print(f"配置文件路径: {config_file_path}")
print(f"配置文件存在: {os.path.exists(config_file_path)}")
print(f"SERPAPI_KEY 状态: {'已配置' if settings.SERPAPI_KEY else '未配置'}")

# 确保日志目录存在
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)