"""
新闻数据模型
"""

from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class NewsSource(str, Enum):
    """新闻来源枚举"""
    BING = "bing"
    SERPAPI = "serpapi"
    RSS = "rss"
    MANUAL = "manual"


class NewsStatus(str, Enum):
    """新闻状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NewsCategory(str, Enum):
    """新闻分类枚举"""
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    SCIENCE = "science"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    POLITICS = "politics"
    WORLD = "world"
    GENERAL = "general"
    OTHER = "other"


class NewsModel(BaseModel):
    """新闻基础模型"""
    id: Optional[str] = Field(None, description="新闻ID")
    title: str = Field(..., description="新闻标题", max_length=500)
    summary: Optional[str] = Field(None, description="新闻摘要", max_length=2000)
    content: Optional[str] = Field(None, description="新闻内容")
    url: HttpUrl = Field(..., description="新闻链接")
    image_url: Optional[HttpUrl] = Field(None, description="新闻图片链接")
    
    # 元数据
    source: NewsSource = Field(default=NewsSource.MANUAL, description="新闻来源")
    author: Optional[str] = Field(None, description="作者", max_length=200)
    publisher: Optional[str] = Field(None, description="发布者", max_length=200)
    category: NewsCategory = Field(default=NewsCategory.OTHER, description="新闻分类")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    
    # 时间信息
    published_at: datetime = Field(..., description="发布时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 状态和统计
    status: NewsStatus = Field(default=NewsStatus.ACTIVE, description="新闻状态")
    view_count: int = Field(default=0, description="查看次数")
    like_count: int = Field(default=0, description="点赞次数")
    share_count: int = Field(default=0, description="分享次数")
    
    # 情感分析结果
    sentiment_score: Optional[float] = Field(None, description="情感分数 (-1 到 1)")
    sentiment_label: Optional[str] = Field(None, description="情感标签")
    
    # 向量化数据
    embedding_id: Optional[str] = Field(None, description="向量ID")
    
    # 额外数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsCreate(BaseModel):
    """创建新闻模型"""
    title: str = Field(..., description="新闻标题", max_length=500)
    summary: Optional[str] = Field(None, description="新闻摘要", max_length=2000)
    content: Optional[str] = Field(None, description="新闻内容")
    url: HttpUrl = Field(..., description="新闻链接")
    image_url: Optional[HttpUrl] = Field(None, description="新闻图片链接")
    
    source: NewsSource = Field(default=NewsSource.MANUAL, description="新闻来源")
    author: Optional[str] = Field(None, description="作者", max_length=200)
    publisher: Optional[str] = Field(None, description="发布者", max_length=200)
    category: NewsCategory = Field(default=NewsCategory.OTHER, description="新闻分类")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    
    published_at: Optional[datetime] = Field(None, description="发布时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class NewsUpdate(BaseModel):
    """更新新闻模型"""
    title: Optional[str] = Field(None, description="新闻标题", max_length=500)
    summary: Optional[str] = Field(None, description="新闻摘要", max_length=2000)
    content: Optional[str] = Field(None, description="新闻内容")
    image_url: Optional[HttpUrl] = Field(None, description="新闻图片链接")
    
    author: Optional[str] = Field(None, description="作者", max_length=200)
    publisher: Optional[str] = Field(None, description="发布者", max_length=200)
    category: Optional[NewsCategory] = Field(None, description="新闻分类")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    
    status: Optional[NewsStatus] = Field(None, description="新闻状态")
    sentiment_score: Optional[float] = Field(None, description="情感分数")
    sentiment_label: Optional[str] = Field(None, description="情感标签")
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    class Config:
        from_attributes = True


class NewsResponse(NewsModel):
    """新闻响应模型"""
    pass


class NewsSearchQuery(BaseModel):
    """新闻搜索查询模型"""
    query: str = Field(..., description="搜索关键词", max_length=200)
    category: Optional[NewsCategory] = Field(None, description="新闻分类")
    source: Optional[NewsSource] = Field(None, description="新闻来源")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    sort_by: str = Field(default="published_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class NewsSearchRequest(BaseModel):
    """智能新闻搜索请求模型 - 支持智能助手"""
    session_id: str = Field(..., description="会话ID")
    keywords: List[str] = Field(..., description="搜索关键词列表")
    num_results: int = Field(default=10, description="搜索结果数量", le=50)
    language: str = Field(default="zh-cn", description="搜索语言")
    country: str = Field(default="cn", description="搜索地区")
    time_period: str = Field(default="1w", description="时间范围: 1d/1w/1m/1y")
    expire_days: int = Field(default=7, description="新闻过期天数，默认7天")


class NewsSearchResponse(BaseModel):
    """新闻搜索响应模型"""
    items: List[NewsResponse] = Field(..., description="新闻列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页面大小")
    has_next: bool = Field(..., description="是否有下一页")


class NewsStats(BaseModel):
    """新闻统计模型"""
    total_news: int = Field(..., description="新闻总数")
    today_news: int = Field(..., description="今日新闻数")
    category_stats: Dict[str, int] = Field(..., description="分类统计")
    source_stats: Dict[str, int] = Field(..., description="来源统计")
    sentiment_stats: Dict[str, int] = Field(..., description="情感统计")
    
    class Config:
        from_attributes = True