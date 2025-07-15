"""
应用配置管理模块
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = Field(default="news-mosaic", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=True, description="调试模式")
    SECRET_KEY: str = Field(default="your-secret-key-here", description="应用密钥")
    
    # API 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务地址")
    PORT: int = Field(default=8000, description="服务端口")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000", description="CORS 允许的源")
    ALLOWED_HOSTS: str = Field(default="localhost,127.0.0.1", description="允许的主机")
    
    # LLM API 配置
    QWEN_API_KEY: str = Field(default="", description="QWEN API 密钥")
    QWEN_BASE_URL: str = Field(default="https://dashscope.aliyuncs.com/api/v1", description="QWEN API 基础URL")
    QWEN_MODEL: str = Field(default="qwen-turbo", description="QWEN 模型")
    
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API 密钥")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API 基础URL")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="DeepSeek 模型")
    
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API 密钥")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", description="OpenAI API 基础URL")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI 模型")
    
    # 新闻搜索 API 配置
    BING_SEARCH_API_KEY: str = Field(default="", description="Bing 搜索 API 密钥")
    BING_SEARCH_ENDPOINT: str = Field(default="https://api.bing.microsoft.com/v7.0/news/search", description="Bing 搜索端点")
    SERPAPI_KEY: str = Field(default="", description="SerpAPI 密钥")
    
    # 向量数据库配置
    PINECONE_API_KEY: str = Field(default="", description="Pinecone API 密钥")
    PINECONE_ENVIRONMENT: str = Field(default="", description="Pinecone 环境")
    PINECONE_INDEX_NAME: str = Field(default="news-embeddings", description="Pinecone 索引名称")
    
    WEAVIATE_URL: str = Field(default="http://localhost:8080", description="Weaviate URL")
    WEAVIATE_API_KEY: str = Field(default="", description="Weaviate API 密钥")
    
    # 数据库配置
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", description="MongoDB 连接URL")
    MONGODB_DB_NAME: str = Field(default="news_mosaic", description="MongoDB 数据库名")
    
    MYSQL_HOST: str = Field(default="localhost", description="MySQL 主机")
    MYSQL_PORT: int = Field(default=3306, description="MySQL 端口")
    MYSQL_USER: str = Field(default="root", description="MySQL 用户")
    MYSQL_PASSWORD: str = Field(default="", description="MySQL 密码")
    MYSQL_DATABASE: str = Field(default="news_mosaic", description="MySQL 数据库")
    
    # Redis 配置
    REDIS_HOST: str = Field(default="localhost", description="Redis 主机")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis 密码")
    REDIS_DB: int = Field(default=0, description="Redis 数据库")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis 连接URL")
    
    # Celery 配置
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery 代理URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery 结果后端")
    
    # 嵌入模型配置
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="嵌入模型")
    EMBEDDING_DIMENSION: int = Field(default=384, description="嵌入向量维度")
    
    # 情感分析配置
    SENTIMENT_MODEL: str = Field(default="cardiffnlp/twitter-roberta-base-sentiment-latest", description="情感分析模型")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存TTL（秒）")
    NEWS_CACHE_TTL: int = Field(default=1800, description="新闻缓存TTL（秒）")
    
    # 定时任务配置
    NEWS_FETCH_INTERVAL: int = Field(default=300, description="新闻获取间隔（秒）")
    NEWS_CLEANUP_INTERVAL: int = Field(default=86400, description="新闻清理间隔（秒）")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件")
    
    # 安全配置
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key", description="JWT 密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间（分钟）")
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, description="最大并发请求数")
    
    # Embedding 配置
    EMBEDDING_MODEL: str = Field(default="text-embedding-v3", description="QWen Embedding 模型")
    EMBEDDING_CHUNK_SIZE: int = Field(default=512, description="文本分块大小（token）")
    EMBEDDING_CHUNK_OVERLAP: int = Field(default=100, description="文本分块重叠（token）")
    EMBEDDING_BATCH_SIZE: int = Field(default=10, description="Embedding 批处理大小")
    EMBEDDING_DIMENSION: int = Field(default=1536, description="向量维度（text-embedding-v3）")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保日志目录存在
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True) 