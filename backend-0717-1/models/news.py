"""
新闻搜索相关数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class NewsSearchRequest(BaseModel):
    """新闻搜索请求模型"""
    session_id: str = Field(..., description="会话ID")
    keywords: List[str] = Field(..., description="搜索关键词列表")
    num_results: int = Field(default=10, description="搜索结果数量", le=50)
    language: str = Field(default="zh-cn", description="搜索语言")
    country: str = Field(default="cn", description="搜索地区")
    time_period: str = Field(default="1d", description="时间范围: 1d/1w/1m")


class NewsSearchResult(BaseModel):
    """新闻搜索结果模型"""
    query: str
    total_found: int
    saved_count: int
    updated_count: int = 0  # 更新的新闻数量（关键词丰富）
    search_time: float
    timestamp: datetime
    news_ids: List[str]
    updated_ids: List[str] = []  # 更新的新闻ID列表
    status: str = "success"
    message: str = ""


class NewsRefreshResult(BaseModel):
    """新闻刷新结果模型"""
    cleaned_count: int = 0  # 清理的过期新闻数量
    refreshed_keywords: List[str] = []  # 重新搜索的关键词
    new_articles_count: int = 0  # 新搜索到的文章数量
    refresh_time: float
    timestamp: datetime
    status: str = "success"
    message: str = ""


class NewsDocument(BaseModel):
    """新闻文档模型（对应数据库结构）"""
    id: str = Field(..., alias="_id")
    session_id: str  # 会话ID
    title: str  # 新闻标题
    date: str  # 新闻发布日期（YYYY-MM-DD格式，用于过期判断）
    category: Optional[str] = None  # 新闻分类（供后续扩展）
    keywords: List[str]  # 关键词列表，会不断丰富
    url: str  # 新闻链接
    source: str  # 新闻来源
    content: str  # 新闻全文内容
    is_embedded: bool = False  # 是否已经向量嵌入
    sentiment: Optional[str] = None  # 情感分析结果（供后续扩展）
    expire_days: int = Field(default=3, description="过期天数，默认3天")
    
    model_config = {"populate_by_name": True}


class NewsStatistics(BaseModel):
    """新闻统计信息模型"""
    session_id: Optional[str] = None
    total_count: int = 0
    today_count: int = 0
    latest_date: Optional[str] = None
    top_keywords: List[Dict[str, Any]] = []
    status: str = "success"


class NewsListResponse(BaseModel):
    """新闻列表响应模型"""
    session_id: str
    news_list: List[Dict[str, Any]] = []
    total_count: int = 0
    returned_count: int = 0
    offset: int = 0
    limit: int = 20
    status: str = "success"
