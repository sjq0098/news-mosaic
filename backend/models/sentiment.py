"""
情感分析数据模型
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SentimentLabel(str, Enum):
    """情感标签枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SentimentConfidence(str, Enum):
    """情感置信度级别"""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


class SentimentAnalysis(BaseModel):
    """情感分析基础模型"""
    id: Optional[str] = Field(None, description="分析ID")
    text: str = Field(..., description="分析文本", max_length=10000)
    
    # 分析结果
    label: SentimentLabel = Field(..., description="情感标签")
    score: float = Field(..., description="情感分数 (-1.0 到 1.0)", ge=-1.0, le=1.0)
    confidence: float = Field(..., description="置信度 (0.0 到 1.0)", ge=0.0, le=1.0)
    confidence_level: SentimentConfidence = Field(..., description="置信度级别")
    
    # 详细分析
    positive_score: Optional[float] = Field(None, description="正面情感分数", ge=0.0, le=1.0)
    negative_score: Optional[float] = Field(None, description="负面情感分数", ge=0.0, le=1.0)
    neutral_score: Optional[float] = Field(None, description="中性情感分数", ge=0.0, le=1.0)
    
    # 关键词和原因
    keywords: List[str] = Field(default_factory=list, description="情感关键词")
    reasons: List[str] = Field(default_factory=list, description="情感判断原因")
    
    # 模型信息
    llm_model: str = Field(..., description="使用的模型名称")
    version: Optional[str] = Field(None, description="模型版本")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    # 关联信息
    news_id: Optional[str] = Field(None, description="关联的新闻ID")
    user_id: Optional[str] = Field(None, description="关联的用户ID")
    
    # 额外元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_confidence_level(self) -> SentimentConfidence:
        """根据置信度分数获取置信度级别"""
        if self.confidence > 0.8:
            return SentimentConfidence.HIGH
        elif self.confidence > 0.5:
            return SentimentConfidence.MEDIUM
        else:
            return SentimentConfidence.LOW


class SentimentAnalysisRequest(BaseModel):
    """情感分析请求模型"""
    text: str = Field(..., description="待分析文本", max_length=10000)
    llm_model: Optional[str] = Field(None, description="指定模型名称")
    include_keywords: bool = Field(default=True, description="是否包含关键词分析")
    include_reasons: bool = Field(default=True, description="是否包含判断原因")
    
    # 关联信息
    news_id: Optional[str] = Field(None, description="关联的新闻ID")
    user_id: Optional[str] = Field(None, description="关联的用户ID")


class SentimentResponse(BaseModel):
    """情感分析响应模型"""
    analysis: SentimentAnalysis = Field(..., description="分析结果")
    processing_time: float = Field(..., description="处理时间（秒）")

    class Config:
        from_attributes = True


class BatchSentimentRequest(BaseModel):
    """批量情感分析请求模型"""
    texts: List[str] = Field(..., description="待分析文本列表", max_items=100)
    llm_model: Optional[str] = Field(None, description="指定模型名称")
    include_keywords: bool = Field(default=True, description="是否包含关键词分析")
    include_reasons: bool = Field(default=True, description="是否包含判断原因")


class BatchSentimentResponse(BaseModel):
    """批量情感分析响应模型"""
    results: List[SentimentAnalysis] = Field(..., description="分析结果列表")
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    processing_time: float = Field(..., description="总处理时间（秒）")

    class Config:
        from_attributes = True


class SentimentStats(BaseModel):
    """情感统计模型"""
    total_analyses: int = Field(..., description="总分析数")
    positive_count: int = Field(..., description="正面情感数")
    negative_count: int = Field(..., description="负面情感数")
    neutral_count: int = Field(..., description="中性情感数")
    mixed_count: int = Field(..., description="混合情感数")
    
    positive_percentage: float = Field(..., description="正面情感占比")
    negative_percentage: float = Field(..., description="负面情感占比")
    neutral_percentage: float = Field(..., description="中性情感占比")
    mixed_percentage: float = Field(..., description="混合情感占比")
    
    average_score: float = Field(..., description="平均情感分数")
    average_confidence: float = Field(..., description="平均置信度")
    
    # 按时间统计
    daily_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="每日统计")
    
    class Config:
        from_attributes = True


class SentimentTrend(BaseModel):
    """情感趋势模型"""
    date: str = Field(..., description="日期")
    positive_count: int = Field(..., description="正面情感数")
    negative_count: int = Field(..., description="负面情感数")
    neutral_count: int = Field(..., description="中性情感数")
    average_score: float = Field(..., description="平均情感分数")

    class Config:
        from_attributes = True 