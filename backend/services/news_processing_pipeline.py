"""
新闻处理流水线服务 - 统一协调所有新闻处理步骤
实现：搜索 → 存储 → 向量化 → AI分析 → 卡片生成 → 情感分析 → 用户记忆更新
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field

from core.database import get_mongodb_database, Collections
from core.config import settings
from services.news_service import NewsService, NewsSearchResult
from services.qwen_service import QWENService
from services.news_card_service import NewsCardService
from services.embedding_service import QWenEmbeddingService
from services.vector_db_service import get_vector_db
from services.sentiment_service import SentimentService
from models.news import NewsModel, NewsSource, NewsCategory
from models.news_card import NewsCard, NewsCardRequest
from models.embedding import EmbeddingResult, TextChunk, ChunkMetadata


class PipelineStage(Enum):
    """流水线阶段枚举"""
    SEARCH = "search"
    STORAGE = "storage"
    VECTORIZATION = "vectorization"
    AI_ANALYSIS = "ai_analysis"
    CARD_GENERATION = "card_generation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    USER_MEMORY_UPDATE = "user_memory_update"
    COMPLETED = "completed"


@dataclass
class PipelineStageResult:
    """流水线阶段结果"""
    stage: PipelineStage
    success: bool
    data: Any = None
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None


class NewsProcessingRequest(BaseModel):
    """新闻处理请求"""
    query: str = Field(..., description="搜索查询")
    user_id: str = Field(default="", description="用户ID")
    
    # 搜索参数
    num_results: int = Field(default=10, ge=1, le=50, description="搜索结果数量")
    language: str = Field(default="zh-cn", description="语言代码")
    country: str = Field(default="cn", description="国家代码")
    time_period: str = Field(default="1d", description="时间范围")
    
    # 处理选项
    enable_storage: bool = Field(default=True, description="是否存储到数据库")
    enable_vectorization: bool = Field(default=True, description="是否进行向量化")
    enable_ai_analysis: bool = Field(default=True, description="是否进行AI分析")
    enable_card_generation: bool = Field(default=True, description="是否生成新闻卡片")
    enable_sentiment_analysis: bool = Field(default=True, description="是否进行情感分析")
    enable_user_memory: bool = Field(default=True, description="是否更新用户记忆")
    
    # 高级选项
    max_cards: int = Field(default=5, ge=1, le=20, description="最大卡片数量")
    include_related_news: bool = Field(default=True, description="是否包含相关新闻")
    personalization_level: float = Field(default=0.5, ge=0.0, le=1.0, description="个性化程度")


class NewsProcessingResponse(BaseModel):
    """新闻处理响应"""
    success: bool
    message: str
    pipeline_id: str
    query: str
    user_id: str
    
    # 处理结果
    total_found: int = 0
    processed_count: int = 0
    cards_generated: int = 0
    vectors_created: int = 0
    
    # 数据
    news_articles: List[Dict[str, Any]] = []
    news_cards: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None
    sentiment_overview: Optional[Dict[str, Any]] = None
    
    # 元数据
    processing_time: float = 0.0
    stage_results: List[Dict[str, Any]] = []
    warnings: List[str] = []
    errors: List[str] = []
    
    # 用户相关
    user_interests_updated: bool = False
    recommended_queries: List[str] = []


class NewsProcessingPipeline:
    """新闻处理流水线 - 核心协调服务"""
    
    def __init__(self):
        self.news_service = None
        self.qwen_service = None
        self.card_service = None
        self.embedding_service = None
        self.vector_db = None
        self.sentiment_service = None
        self.db = None
        
    async def _initialize_services(self):
        """初始化所有服务"""
        if not self.news_service:
            self.news_service = NewsService()
            self.qwen_service = QWENService()
            self.card_service = NewsCardService()
            self.embedding_service = QWenEmbeddingService()
            self.vector_db = get_vector_db()
            self.sentiment_service = SentimentService()
            self.db = await get_mongodb_database()
    
    async def process_news_pipeline(self, request: NewsProcessingRequest) -> NewsProcessingResponse:
        """
        执行完整的新闻处理流水线
        """
        pipeline_id = str(uuid.uuid4())
        start_time = time.time()
        stage_results = []
        warnings = []
        errors = []
        
        logger.info(f"开始新闻处理流水线 {pipeline_id}: query='{request.query}', user_id={request.user_id}")
        
        try:
            # 初始化服务
            await self._initialize_services()
            
            # 阶段1: 搜索新闻
            search_result = await self._execute_stage(
                PipelineStage.SEARCH,
                self._search_news,
                request
            )
            stage_results.append(search_result.__dict__)
            
            if not search_result.success:
                return self._build_error_response(pipeline_id, request, "新闻搜索失败", stage_results)
            
            articles = search_result.data.articles
            if not articles:
                return self._build_error_response(pipeline_id, request, "未找到相关新闻", stage_results)
            
            # 阶段2: 存储新闻
            storage_result = None
            stored_news = []
            if request.enable_storage:
                storage_result = await self._execute_stage(
                    PipelineStage.STORAGE,
                    self._store_news,
                    articles, request.user_id
                )
                stage_results.append(storage_result.__dict__)
                stored_news = storage_result.data if storage_result.success else []
            
            # 阶段3: 向量化
            vectorization_result = None
            if request.enable_vectorization and stored_news:
                vectorization_result = await self._execute_stage(
                    PipelineStage.VECTORIZATION,
                    self._vectorize_news,
                    stored_news
                )
                stage_results.append(vectorization_result.__dict__)
            
            # 阶段4: AI分析
            ai_analysis_result = None
            if request.enable_ai_analysis:
                ai_analysis_result = await self._execute_stage(
                    PipelineStage.AI_ANALYSIS,
                    self._generate_ai_analysis,
                    articles, request.query, request.user_id
                )
                stage_results.append(ai_analysis_result.__dict__)
            
            # 阶段5: 生成新闻卡片
            card_generation_result = None
            news_cards = []
            if request.enable_card_generation and stored_news:
                card_generation_result = await self._execute_stage(
                    PipelineStage.CARD_GENERATION,
                    self._generate_news_cards,
                    stored_news[:request.max_cards], request
                )
                stage_results.append(card_generation_result.__dict__)
                news_cards = card_generation_result.data if card_generation_result.success else []
            
            # 阶段6: 情感分析
            sentiment_result = None
            if request.enable_sentiment_analysis:
                sentiment_result = await self._execute_stage(
                    PipelineStage.SENTIMENT_ANALYSIS,
                    self._analyze_sentiment_overview,
                    articles
                )
                stage_results.append(sentiment_result.__dict__)
            
            # 阶段7: 更新用户记忆
            memory_result = None
            if request.enable_user_memory:
                memory_result = await self._execute_stage(
                    PipelineStage.USER_MEMORY_UPDATE,
                    self._update_user_memory,
                    request.user_id, request.query, articles, news_cards
                )
                stage_results.append(memory_result.__dict__)
            
            # 构建成功响应
            processing_time = time.time() - start_time
            
            return NewsProcessingResponse(
                success=True,
                message="新闻处理流水线执行成功",
                pipeline_id=pipeline_id,
                query=request.query,
                user_id=request.user_id,
                total_found=len(articles),
                processed_count=len(stored_news),
                cards_generated=len(news_cards),
                vectors_created=vectorization_result.data if vectorization_result and vectorization_result.success else 0,
                news_articles=stored_news if stored_news else [article.__dict__ if hasattr(article, '__dict__') else article for article in articles],
                news_cards=[card.__dict__ if hasattr(card, '__dict__') else card for card in news_cards],
                ai_summary=ai_analysis_result.data if ai_analysis_result and ai_analysis_result.success else None,
                sentiment_overview=sentiment_result.data if sentiment_result and sentiment_result.success else None,
                processing_time=processing_time,
                stage_results=stage_results,
                warnings=warnings,
                errors=errors,
                user_interests_updated=memory_result.success if memory_result else False,
                recommended_queries=await self._generate_recommended_queries(request.user_id, request.query)
            )
            
        except Exception as e:
            logger.error(f"新闻处理流水线执行失败 {pipeline_id}: {e}")
            return self._build_error_response(pipeline_id, request, f"流水线执行失败: {str(e)}", stage_results)

    async def _execute_stage(self, stage: PipelineStage, func, *args) -> PipelineStageResult:
        """执行流水线阶段"""
        start_time = time.time()
        logger.info(f"执行阶段: {stage.value}")

        try:
            result = await func(*args)
            processing_time = time.time() - start_time

            logger.info(f"阶段 {stage.value} 执行成功，耗时: {processing_time:.2f}s")
            return PipelineStageResult(
                stage=stage,
                success=True,
                data=result,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"阶段 {stage.value} 执行失败: {str(e)}"
            logger.error(error_msg)

            return PipelineStageResult(
                stage=stage,
                success=False,
                error=error_msg,
                processing_time=processing_time
            )

    async def _search_news(self, request: NewsProcessingRequest) -> NewsSearchResult:
        """阶段1: 搜索新闻"""
        return await self.news_service.search_news(
            query=request.query,
            num_results=request.num_results,
            language=request.language,
            country=request.country,
            time_period=request.time_period
        )

    async def _store_news(self, articles: List[Any], user_id: str) -> List[Dict[str, Any]]:
        """阶段2: 存储新闻到数据库"""
        stored_news = []

        for article in articles:
            try:
                # 检查是否已存在
                existing = await self.db[Collections.NEWS].find_one({
                    "title": article.title,
                    "url": str(article.link)
                })

                if existing:
                    stored_news.append(existing)
                    continue

                # 解析发布时间
                published_at = datetime.utcnow()
                if hasattr(article, 'date') and article.date:
                    try:
                        from dateutil import parser
                        published_at = parser.parse(article.date)
                    except:
                        published_at = datetime.utcnow()

                # 创建新闻文档
                news_doc = {
                    "_id": str(uuid.uuid4()),
                    "title": article.title,
                    "content": article.snippet,
                    "url": str(article.link),
                    "image_url": str(article.thumbnail) if hasattr(article, 'thumbnail') and article.thumbnail else None,
                    "source": article.source,
                    "category": NewsCategory.GENERAL.value,
                    "published_at": published_at,
                    "created_at": datetime.utcnow(),
                    "created_by": user_id,
                    "tags": [],
                    "view_count": 0,
                    "like_count": 0,
                    "metadata": {
                        "search_query": "",
                        "relevance_score": 0.0
                    }
                }

                # 插入数据库
                await self.db[Collections.NEWS].insert_one(news_doc)
                stored_news.append(news_doc)

            except Exception as e:
                logger.error(f"存储新闻失败: {e}")
                continue

        logger.info(f"成功存储 {len(stored_news)} 条新闻")
        return stored_news

    async def _vectorize_news(self, news_list: List[Dict[str, Any]]) -> int:
        """阶段3: 新闻向量化"""
        vectors_created = 0

        # 限制向量化的新闻数量以提高性能
        max_vectorize = min(len(news_list), 20)  # 最多处理20条
        limited_news_list = news_list[:max_vectorize]

        logger.info(f"开始向量化 {len(limited_news_list)} 条新闻（总共 {len(news_list)} 条）")

        for news in limited_news_list:
            try:
                # 准备文本内容
                text_content = f"{news['title']}\n{news.get('content', '')}"

                # 创建文本块
                chunk = TextChunk(
                    content=text_content,
                    chunk_index=0,
                    metadata=ChunkMetadata(
                        source_id=news["_id"],
                        title=news["title"],
                        published_at=news.get("published_at"),
                        url=news.get("url"),
                        source=news.get("source")
                    )
                )

                # 生成嵌入向量
                embedding = await self.embedding_service.get_embeddings([text_content])
                if embedding and len(embedding) > 0:
                    embedding_result = EmbeddingResult(
                        chunk=chunk,
                        embedding=embedding[0],
                        model_info={"source_id": news["_id"]}
                    )

                    # 存储到向量数据库
                    self.vector_db.upsert_embeddings([embedding_result])
                    vectors_created += 1

            except Exception as e:
                logger.error(f"向量化新闻失败 {news.get('_id', 'unknown')}: {e}")
                continue

        logger.info(f"成功创建 {vectors_created} 个向量")
        return vectors_created

    async def _generate_ai_analysis(self, articles: List[Any], query: str, user_id: str) -> str:
        """阶段4: 生成AI分析摘要"""
        # 构建分析提示词
        articles_text = "\n\n".join([
            f"标题: {article.title}\n内容: {article.snippet}"
            for article in articles[:5]  # 限制文章数量避免token过多
        ])

        prompt = f"""
        基于以下新闻内容，为用户查询"{query}"生成一个综合分析摘要：

        新闻内容：
        {articles_text}

        请提供：
        1. 主要事件概述
        2. 关键趋势分析
        3. 重要观点提炼
        4. 潜在影响评估

        要求：
        - 客观中立，基于事实
        - 结构清晰，逻辑连贯
        - 突出与查询相关的重点
        - 控制在300字以内
        """

        response = await self.qwen_service.generate_response(
            user_message=prompt,
            temperature=0.3,
            max_tokens=500
        )

        return response.content

    async def _generate_news_cards(self, news_list: List[Dict[str, Any]], request: NewsProcessingRequest) -> List[Dict[str, Any]]:
        """阶段5: 生成新闻卡片"""
        cards = []

        for news in news_list:
            try:
                logger.info(f"开始生成新闻卡片: {news.get('_id', 'unknown')} - {news.get('title', 'N/A')}")

                card_request = NewsCardRequest(
                    news_id=news["_id"],
                    include_sentiment=request.enable_sentiment_analysis,
                    include_entities=True,
                    include_related=request.include_related_news,
                    max_summary_length=200
                )

                card_response = await self.card_service.generate_card(card_request)
                if card_response and card_response.card:
                    cards.append(card_response.card.__dict__)
                    logger.info(f"成功生成新闻卡片: {news.get('_id', 'unknown')}")
                else:
                    logger.warning(f"卡片生成返回空结果: {news.get('_id', 'unknown')}")

            except Exception as e:
                logger.error(f"生成新闻卡片失败 {news.get('_id', 'unknown')}: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                continue

        logger.info(f"成功生成 {len(cards)} 张新闻卡片")
        return cards

    async def _analyze_sentiment_overview(self, articles: List[Any]) -> Dict[str, Any]:
        """阶段6: 情感分析概览"""
        sentiments = []

        for article in articles:
            try:
                sentiment_result = await self.sentiment_service.analyze_text(
                    text=f"{article.title} {article.snippet}",
                    language="zh"
                )
                sentiments.append(sentiment_result)

            except Exception as e:
                logger.error(f"情感分析失败: {e}")
                continue

        # 统计情感分布
        positive_count = sum(1 for s in sentiments if s.get("label") == "positive")
        negative_count = sum(1 for s in sentiments if s.get("label") == "negative")
        neutral_count = len(sentiments) - positive_count - negative_count

        total = len(sentiments)
        if total == 0:
            return {"error": "无法进行情感分析"}

        return {
            "total_analyzed": total,
            "positive": {
                "count": positive_count,
                "percentage": round(positive_count / total * 100, 2)
            },
            "negative": {
                "count": negative_count,
                "percentage": round(negative_count / total * 100, 2)
            },
            "neutral": {
                "count": neutral_count,
                "percentage": round(neutral_count / total * 100, 2)
            },
            "overall_sentiment": "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral"
        }

    async def _update_user_memory(self, user_id: str, query: str, articles: List[Any], cards: List[Dict[str, Any]]) -> bool:
        """阶段7: 更新用户记忆"""
        try:
            # 如果没有用户ID，跳过用户记忆更新
            if not user_id or user_id == "demo_user":
                logger.info("跳过用户记忆更新（演示模式或无用户ID）")
                return True

            # 记录搜索历史（简化版本）
            search_record = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "query": query,
                "timestamp": datetime.utcnow(),
                "results_count": len(articles),
                "cards_generated": len(cards)
            }

            await self.db[Collections.SEARCH_HISTORY].insert_one(search_record)
            logger.info(f"用户记忆更新完成: {user_id}")

            return True

        except Exception as e:
            logger.error(f"更新用户记忆失败: {e}")
            return False

    async def _update_user_interests(self, user_id: str, query: str, articles: List[Any]):
        """更新用户兴趣标签"""
        try:
            # 提取关键词
            keywords = await self._extract_keywords_from_articles(articles)

            # 获取现有兴趣
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs:
                user_prefs = {
                    "user_id": user_id,
                    "interests": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

            # 更新兴趣权重
            interests = user_prefs.get("interests", {})
            for keyword in keywords:
                interests[keyword] = interests.get(keyword, 0) + 1

            # 保持兴趣数量在合理范围内
            if len(interests) > 50:
                # 保留权重最高的50个兴趣
                sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
                interests = dict(sorted_interests[:50])

            user_prefs["interests"] = interests
            user_prefs["updated_at"] = datetime.utcnow()

            # 更新或插入
            await self.db[Collections.USER_PREFERENCES].replace_one(
                {"user_id": user_id},
                user_prefs,
                upsert=True
            )

        except Exception as e:
            logger.error(f"更新用户兴趣失败: {e}")

    async def _extract_keywords_from_articles(self, articles: List[Any]) -> List[str]:
        """从文章中提取关键词"""
        # 简单的关键词提取，实际项目中可以使用更复杂的NLP技术
        keywords = set()

        for article in articles:
            # 从标题和内容中提取关键词
            text = f"{article.title} {article.snippet}".lower()

            # 简单的关键词提取（可以改进）
            words = text.split()
            for word in words:
                if len(word) > 2 and word.isalpha():
                    keywords.add(word)

        return list(keywords)[:20]  # 限制关键词数量

    async def _record_user_activity(self, user_id: str, activity_type: str, metadata: Dict[str, Any]):
        """记录用户活动"""
        try:
            activity_record = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": datetime.utcnow(),
                "metadata": metadata
            }

            await self.db[Collections.API_LOGS].insert_one(activity_record)

        except Exception as e:
            logger.error(f"记录用户活动失败: {e}")

    async def _generate_recommended_queries(self, user_id: str, current_query: str) -> List[str]:
        """生成推荐查询"""
        try:
            # 基于用户兴趣生成推荐
            user_prefs = await self.db[Collections.USER_PREFERENCES].find_one({"user_id": user_id})
            if not user_prefs or not user_prefs.get("interests"):
                return ["科技新闻", "财经动态", "社会热点", "国际新闻"]

            # 获取用户最感兴趣的话题
            interests = user_prefs["interests"]
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:5]

            recommendations = []
            for interest, _ in top_interests:
                recommendations.append(f"{interest}最新动态")

            return recommendations

        except Exception as e:
            logger.error(f"生成推荐查询失败: {e}")
            return ["热门新闻", "今日要闻", "科技资讯"]

    def _build_error_response(self, pipeline_id: str, request: NewsProcessingRequest,
                            error_message: str, stage_results: List[Dict[str, Any]]) -> NewsProcessingResponse:
        """构建错误响应"""
        return NewsProcessingResponse(
            success=False,
            message=error_message,
            pipeline_id=pipeline_id,
            query=request.query,
            user_id=request.user_id,
            stage_results=stage_results,
            errors=[error_message]
        )


# 全局实例
news_pipeline = NewsProcessingPipeline()


async def get_news_pipeline() -> NewsProcessingPipeline:
    """获取新闻处理流水线实例"""
    return news_pipeline
