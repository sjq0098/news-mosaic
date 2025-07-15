"""
情感分析服务 - 处理情感分析相关的业务逻辑
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib

from models.sentiment import (
    SentimentResponse, SentimentAnalysisRequest, BatchSentimentRequest,
    BatchSentimentResponse, SentimentStats, SentimentTrend, SentimentAnalysis
)
from core.database import get_mongodb_database
from core.config import settings
from core.cache import cache, CacheKeys


class SentimentService:
    """情感分析服务类"""
    
    def __init__(self):
        self.db = None
        self.available_models = ["basic", "bert", "roberta"]
        self.default_model = "basic"
    
    async def _get_db(self):
        """获取数据库连接"""
        if self.db is None:
            self.db = await get_mongodb_database()
        return self.db
    
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentResponse:
        """执行单文本情感分析"""
        try:
            # 简单的情感分析逻辑（实际应用中应该使用深度学习模型）
            sentiment_score = self._calculate_sentiment_score(request.text)
            
            # 确定情感标签
            if sentiment_score > 0.1:
                label = "positive"
            elif sentiment_score < -0.1:
                label = "negative"
            else:
                label = "neutral"
            
            # 创建分析结果
            analysis = SentimentAnalysis(
                id=str(uuid.uuid4()),
                text=request.text,
                sentiment_label=label,
                confidence_score=abs(sentiment_score),
                sentiment_score=sentiment_score,
                model_used=request.model or self.default_model,
                analysis_time=datetime.utcnow(),
                user_id=request.user_id,
                news_id=request.news_id,
                metadata=request.metadata or {}
            )
            
            return SentimentResponse(
                success=True,
                analysis=analysis,
                processing_time=0.1  # 模拟处理时间
            )
            
        except Exception as e:
            return SentimentResponse(
                success=False,
                error=f"情感分析失败: {str(e)}",
                processing_time=0.0
            )
    
    async def batch_analyze_sentiment(self, request: BatchSentimentRequest) -> BatchSentimentResponse:
        """执行批量文本情感分析"""
        try:
            results = []
            total_processing_time = 0.0
            
            for text in request.texts:
                # 为每个文本创建分析请求
                analysis_request = SentimentAnalysisRequest(
                    text=text,
                    model=request.model,
                    user_id=request.user_id,
                    metadata=request.metadata
                )
                
                # 执行分析
                result = await self.analyze_sentiment(analysis_request)
                results.append(result.analysis)
                total_processing_time += result.processing_time
            
            return BatchSentimentResponse(
                success=True,
                results=results,
                total_count=len(request.texts),
                processing_time=total_processing_time
            )
            
        except Exception as e:
            return BatchSentimentResponse(
                success=False,
                error=f"批量情感分析失败: {str(e)}",
                results=[],
                total_count=0,
                processing_time=0.0
            )
    
    async def get_news_sentiment(self, news_id: str) -> Optional[SentimentResponse]:
        """获取新闻的情感分析结果"""
        try:
            db = await self._get_db()
            analysis = await db.sentiment_analyses.find_one({"news_id": news_id})
            
            if analysis:
                sentiment_analysis = SentimentAnalysis(**analysis)
                return SentimentResponse(
                    success=True,
                    analysis=sentiment_analysis,
                    processing_time=0.0
                )
            
            return None
            
        except Exception:
            return None
    
    async def analyze_news_sentiment(self, news_id: str) -> SentimentResponse:
        """分析指定新闻的情感"""
        try:
            db = await self._get_db()
            # 获取新闻内容
            news = await db.news.find_one({"id": news_id})
            if not news:
                raise Exception("新闻不存在")
            
            # 分析新闻标题和内容
            text = f"{news.get('title', '')} {news.get('content', '')}"
            
            request = SentimentAnalysisRequest(
                text=text,
                news_id=news_id,
                metadata={"source": "news_analysis"}
            )
            
            return await self.analyze_sentiment(request)
            
        except Exception as e:
            return SentimentResponse(
                success=False,
                error=f"新闻情感分析失败: {str(e)}",
                processing_time=0.0
            )
    
    async def save_analysis_result(self, analysis: SentimentAnalysis):
        """保存分析结果到数据库"""
        try:
            db = await self._get_db()
            analysis_dict = analysis.dict()
            await db.sentiment_analyses.insert_one(analysis_dict)
        except Exception:
            pass  # 静默失败，不影响主要流程
    
    async def cache_batch_results(self, texts: List[str], results: List[SentimentAnalysis]):
        """缓存批量分析结果"""
        try:
            for text, result in zip(texts, results):
                cache_key = f"{CacheKeys.SENTIMENT_RESULT}{hash(text)}"
                await cache.set(cache_key, result.dict(), expire=3600)
        except Exception:
            pass  # 静默失败
    
    async def get_sentiment_stats(self, days: int = 7, category: Optional[str] = None) -> SentimentStats:
        """获取情感分析统计信息"""
        try:
            db = await self._get_db()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            query = {"analysis_time": {"$gte": start_date}}
            if category:
                query["metadata.category"] = category
            
            # 统计各种情感
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$sentiment_label",
                    "count": {"$sum": 1}
                }}
            ]
            
            cursor = db.sentiment_analyses.aggregate(pipeline)
            sentiment_counts = {}
            total_analyses = 0
            
            async for doc in cursor:
                sentiment_counts[doc["_id"]] = doc["count"]
                total_analyses += doc["count"]
            
            return SentimentStats(
                total_analyses=total_analyses,
                positive_count=sentiment_counts.get("positive", 0),
                negative_count=sentiment_counts.get("negative", 0),
                neutral_count=sentiment_counts.get("neutral", 0),
                average_confidence=0.75,  # 模拟平均置信度
                period_days=days,
                category=category
            )
            
        except Exception:
            return SentimentStats(
                total_analyses=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                average_confidence=0.0,
                period_days=days,
                category=category
            )
    
    async def get_sentiment_trends(self, days: int = 30, category: Optional[str] = None) -> List[SentimentTrend]:
        """获取情感趋势数据"""
        try:
            db = await self._get_db()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            query = {"analysis_time": {"$gte": start_date}}
            if category:
                query["metadata.category"] = category
            
            # 按日期分组统计
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$analysis_time"}},
                        "sentiment": "$sentiment_label"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.date": 1}}
            ]
            
            cursor = db.sentiment_analyses.aggregate(pipeline)
            trends_data = {}
            
            async for doc in cursor:
                date = doc["_id"]["date"]
                sentiment = doc["_id"]["sentiment"]
                count = doc["count"]
                
                if date not in trends_data:
                    trends_data[date] = {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    }
                
                trends_data[date][sentiment] = count
            
            # 转换为趋势对象列表
            trends = []
            for date, counts in trends_data.items():
                total = sum(counts.values())
                trends.append(SentimentTrend(
                    date=datetime.strptime(date, "%Y-%m-%d").date(),
                    positive_count=counts["positive"],
                    negative_count=counts["negative"],
                    neutral_count=counts["neutral"],
                    total_count=total,
                    positive_ratio=counts["positive"] / total if total > 0 else 0.0
                ))
            
            return trends
            
        except Exception:
            return []
    
    async def get_available_models(self) -> List[str]:
        """获取可用的情感分析模型列表"""
        return self.available_models
    
    async def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """获取模型性能指标"""
        if model_name not in self.available_models:
            raise Exception("模型不存在")
        
        # 模拟模型性能数据
        performance = {
            "model_name": model_name,
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "last_updated": datetime.utcnow().isoformat(),
            "total_predictions": 10000,
            "training_data_size": 50000
        }
        
        return performance
    
    async def submit_feedback(self, analysis_id: str, correct_label: str, feedback_text: Optional[str] = None) -> bool:
        """提交情感分析反馈"""
        try:
            db = await self._get_db()
            
            # 检查分析结果是否存在
            analysis = await db.sentiment_analyses.find_one({"id": analysis_id})
            if not analysis:
                return False
            
            # 保存反馈
            feedback = {
                "id": str(uuid.uuid4()),
                "analysis_id": analysis_id,
                "original_label": analysis["sentiment_label"],
                "correct_label": correct_label,
                "feedback_text": feedback_text,
                "submitted_at": datetime.utcnow()
            }
            
            await db.sentiment_feedback.insert_one(feedback)
            return True
            
        except Exception:
            return False
    
    async def delete_analysis(self, analysis_id: str) -> bool:
        """删除情感分析结果"""
        try:
            db = await self._get_db()
            result = await db.sentiment_analyses.delete_one({"id": analysis_id})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def retrain_model(self, model_name: str):
        """重新训练情感分析模型（后台任务）"""
        try:
            # 模拟模型重训练过程
            # 实际应用中这里会包含复杂的机器学习流程
            print(f"开始重训练模型: {model_name}")
            # 这里可以添加实际的模型训练代码
            print(f"模型 {model_name} 重训练完成")
        except Exception as e:
            print(f"模型重训练失败: {str(e)}")
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """计算情感分数（简单的基于关键词的方法）"""
        # 这是一个简化的情感分析实现
        # 实际应用中应该使用更复杂的模型
        
        positive_words = ["好", "棒", "优秀", "喜欢", "满意", "高兴", "开心", "赞", "不错", "很棒"]
        negative_words = ["坏", "差", "糟糕", "讨厌", "失望", "生气", "愤怒", "烦", "恶心", "垃圾"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # 计算情感分数
        if positive_count + negative_count == 0:
            return 0.0
        
        score = (positive_count - negative_count) / (positive_count + negative_count)
        
        # 添加一些随机性来模拟真实模型的复杂性
        import random
        score += random.uniform(-0.1, 0.1)
        
        # 确保分数在 -1 到 1 之间
        return max(-1.0, min(1.0, score))