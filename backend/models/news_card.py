"""
新闻结构化卡片模型
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from models.sentiment import SentimentLabel, SentimentConfidence
from models.news import NewsCategory, NewsSource


class ImportanceLevel(str, Enum):
    """重要性级别枚举"""
    CRITICAL = "critical"      # 9-10分，重大突发新闻
    HIGH = "high"             # 7-8分，重要新闻  
    MEDIUM = "medium"         # 5-6分，一般新闻
    LOW = "low"               # 3-4分，普通新闻
    MINIMAL = "minimal"       # 1-2分，次要新闻


class CredibilityLevel(str, Enum):
    """可信度级别枚举"""
    VERIFIED = "verified"     # 官方来源，权威媒体
    RELIABLE = "reliable"     # 知名媒体，可信来源
    MODERATE = "moderate"     # 一般来源，需要验证
    QUESTIONABLE = "questionable"  # 来源可疑，需要谨慎
    UNVERIFIED = "unverified"      # 未验证来源


class NewsTheme(BaseModel):
    """新闻主题分析"""
    primary_theme: str = Field(..., description="主要主题", max_length=100)
    secondary_themes: List[str] = Field(default_factory=list, description="次要主题")
    theme_confidence: float = Field(..., description="主题置信度", ge=0.0, le=1.0)


class EntityMention(BaseModel):
    """实体提及"""
    entity: str = Field(..., description="实体名称", max_length=200)
    entity_type: str = Field(..., description="实体类型（人名、地名、机构等）", max_length=50)
    mention_count: int = Field(default=1, description="提及次数")
    confidence: float = Field(..., description="识别置信度", ge=0.0, le=1.0)


class NewsCardMetadata(BaseModel):
    """新闻卡片元数据"""
    
    # 基础信息
    news_id: str = Field(..., description="新闻ID")
    card_id: Optional[str] = Field(None, description="卡片ID")
    
    # 内容分析
    summary: str = Field(..., description="智能摘要", max_length=500)
    enhanced_summary: str = Field(..., description="增强摘要（包含背景信息）", max_length=1000)
    key_points: List[str] = Field(default_factory=list, description="核心要点")
    
    # 关键词和主题
    keywords: List[str] = Field(default_factory=list, description="关键词")
    hashtags: List[str] = Field(default_factory=list, description="推荐标签")
    themes: NewsTheme = Field(..., description="主题分析")
    
    # 情感分析
    sentiment_label: SentimentLabel = Field(..., description="情感标签")
    sentiment_score: float = Field(..., description="情感分数", ge=-1.0, le=1.0)
    sentiment_confidence: SentimentConfidence = Field(..., description="情感置信度")
    emotional_keywords: List[str] = Field(default_factory=list, description="情感关键词")
    
    # 重要性分析
    importance_score: float = Field(..., description="重要性分数", ge=0.0, le=10.0)
    importance_level: ImportanceLevel = Field(..., description="重要性级别")
    importance_reasons: List[str] = Field(default_factory=list, description="重要性判断原因")
    
    # 可信度分析
    credibility_score: float = Field(..., description="可信度分数", ge=0.0, le=10.0)
    credibility_level: CredibilityLevel = Field(..., description="可信度级别")
    credibility_factors: List[str] = Field(default_factory=list, description="可信度影响因素")
    
    # 实体识别
    entities: List[EntityMention] = Field(default_factory=list, description="实体提及")
    people: List[str] = Field(default_factory=list, description="相关人物")
    organizations: List[str] = Field(default_factory=list, description="相关机构")
    locations: List[str] = Field(default_factory=list, description="相关地点")
    
    # 时效性
    urgency_score: float = Field(..., description="紧急程度", ge=0.0, le=10.0)
    freshness_score: float = Field(..., description="新鲜度", ge=0.0, le=10.0)
    time_sensitivity: bool = Field(default=False, description="是否时效性敏感")
    
    # 推荐信息
    target_audience: List[str] = Field(default_factory=list, description="目标受众")
    reading_time_minutes: int = Field(..., description="预估阅读时长（分钟）")
    difficulty_level: str = Field(default="medium", description="阅读难度", pattern="^(easy|medium|hard)$")
    
    # 相关性
    related_news_ids: List[str] = Field(default_factory=list, description="相关新闻ID")
    similarity_scores: Dict[str, float] = Field(default_factory=dict, description="相似度分数")
    
    # 生成信息
    generation_model: str = Field(..., description="生成模型")
    generation_time: float = Field(..., description="生成耗时（秒）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 额外元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_importance_level(self) -> ImportanceLevel:
        """根据重要性分数获取重要性级别"""
        if self.importance_score >= 9.0:
            return ImportanceLevel.CRITICAL
        elif self.importance_score >= 7.0:
            return ImportanceLevel.HIGH
        elif self.importance_score >= 5.0:
            return ImportanceLevel.MEDIUM
        elif self.importance_score >= 3.0:
            return ImportanceLevel.LOW
        else:
            return ImportanceLevel.MINIMAL

    def get_credibility_level(self) -> CredibilityLevel:
        """根据可信度分数获取可信度级别"""
        if self.credibility_score >= 9.0:
            return CredibilityLevel.VERIFIED
        elif self.credibility_score >= 7.0:
            return CredibilityLevel.RELIABLE
        elif self.credibility_score >= 5.0:
            return CredibilityLevel.MODERATE
        elif self.credibility_score >= 3.0:
            return CredibilityLevel.QUESTIONABLE
        else:
            return CredibilityLevel.UNVERIFIED


class NewsCard(BaseModel):
    """完整的新闻卡片模型"""
    
    # 基础新闻信息
    news_id: str = Field(..., description="新闻ID")
    title: str = Field(..., description="新闻标题")
    url: str = Field(..., description="新闻链接")
    image_url: Optional[str] = Field(None, description="新闻图片")
    source: NewsSource = Field(..., description="新闻来源")
    category: NewsCategory = Field(..., description="新闻分类")
    published_at: datetime = Field(..., description="发布时间")
    
    # 结构化元数据
    metadata: NewsCardMetadata = Field(..., description="卡片元数据")
    
    # 显示配置
    is_featured: bool = Field(default=False, description="是否为特色新闻")
    display_priority: int = Field(default=0, description="显示优先级")
    color_theme: Optional[str] = Field(None, description="颜色主题")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsCardRequest(BaseModel):
    """新闻卡片生成请求"""
    news_id: str = Field(..., description="新闻ID")
    include_sentiment: bool = Field(default=True, description="是否包含情感分析")
    include_entities: bool = Field(default=True, description="是否包含实体识别")
    include_related: bool = Field(default=True, description="是否查找相关新闻")
    max_summary_length: int = Field(default=300, ge=50, le=1000, description="摘要最大长度")
    generation_model: Optional[str] = Field(None, description="指定生成模型")


class NewsCardResponse(BaseModel):
    """新闻卡片生成响应"""
    card: NewsCard = Field(..., description="生成的新闻卡片")
    processing_time: float = Field(..., description="处理时间（秒）")
    warnings: List[str] = Field(default_factory=list, description="警告信息")

    class Config:
        from_attributes = True


class BatchNewsCardRequest(BaseModel):
    """批量新闻卡片生成请求"""
    news_ids: List[str] = Field(..., description="新闻ID列表", max_items=50)
    include_sentiment: bool = Field(default=True, description="是否包含情感分析")
    include_entities: bool = Field(default=True, description="是否包含实体识别")
    include_related: bool = Field(default=True, description="是否查找相关新闻")
    max_summary_length: int = Field(default=300, ge=50, le=1000, description="摘要最大长度")
    generation_model: Optional[str] = Field(None, description="指定生成模型")


class BatchNewsCardResponse(BaseModel):
    """批量新闻卡片生成响应"""
    cards: List[NewsCard] = Field(..., description="生成的新闻卡片列表")
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    processing_time: float = Field(..., description="总处理时间（秒）")
    failed_news_ids: List[str] = Field(default_factory=list, description="失败的新闻ID")

    class Config:
        from_attributes = True


class NewsCardStats(BaseModel):
    """新闻卡片统计"""
    total_cards: int = Field(..., description="卡片总数")
    sentiment_distribution: Dict[str, int] = Field(..., description="情感分布")
    importance_distribution: Dict[str, int] = Field(..., description="重要性分布")
    category_distribution: Dict[str, int] = Field(..., description="分类分布")
    average_importance: float = Field(..., description="平均重要性")
    average_credibility: float = Field(..., description="平均可信度")
    
    class Config:
        from_attributes = True 