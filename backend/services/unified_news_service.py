"""
统一新闻处理服务
整合 SerpAPI 搜索、MongoDB 存储、通义千问分析和新闻卡片生成
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from loguru import logger

from core.database import get_mongodb_database, Collections
from services.news_service import NewsService
from services.qwen_service import QWENService
from services.news_card_service import NewsCardService
from models.news import NewsModel, NewsSource, NewsCategory
from models.news_card import NewsCardRequest


class UnifiedNewsRequest(BaseModel):
    """统一新闻处理请求"""
    query: str = Field(..., description="搜索查询")
    user_id: str = Field(..., description="用户ID")
    
    # 搜索选项
    num_results: int = Field(default=10, ge=1, le=50, description="搜索结果数量")
    language: str = Field(default="zh-cn", description="语言")
    country: str = Field(default="cn", description="国家")
    time_period: str = Field(default="1d", description="时间范围")
    
    # 处理选项
    enable_storage: bool = Field(default=True, description="是否存储到数据库")
    enable_analysis: bool = Field(default=True, description="是否进行AI分析")
    enable_cards: bool = Field(default=True, description="是否生成新闻卡片")
    
    # 分析选项
    max_cards: int = Field(default=5, ge=1, le=10, description="最大卡片数量")
    include_sentiment: bool = Field(default=True, description="包含情感分析")
    include_summary: bool = Field(default=True, description="包含摘要")


class UnifiedNewsResponse(BaseModel):
    """统一新闻处理响应"""
    success: bool = Field(..., description="处理是否成功")
    message: str = Field(..., description="处理消息")
    
    # 搜索结果
    query: str = Field(..., description="搜索查询")
    total_found: int = Field(..., description="找到的新闻总数")
    processed_count: int = Field(..., description="处理的新闻数量")
    
    # 处理结果
    news_articles: List[Dict[str, Any]] = Field(default_factory=list, description="新闻文章")
    news_cards: List[Dict[str, Any]] = Field(default_factory=list, description="新闻卡片")
    ai_summary: Optional[str] = Field(None, description="AI生成的总结")
    
    # 统计信息
    processing_time: float = Field(..., description="处理时间(秒)")
    storage_count: int = Field(default=0, description="存储的新闻数量")
    cards_generated: int = Field(default=0, description="生成的卡片数量")
    
    # 错误信息
    errors: List[str] = Field(default_factory=list, description="处理过程中的错误")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class UnifiedNewsService:
    """统一新闻处理服务"""
    
    def __init__(self):
        self.news_service = None
        self.qwen_service = None
        self.card_service = None

    async def _get_services(self):
        """获取所需的服务实例"""
        if not self.news_service:
            self.news_service = NewsService()
        if not self.qwen_service:
            self.qwen_service = QWENService()
        if not self.card_service:
            self.card_service = NewsCardService()
    
    async def process_news_unified(self, request: UnifiedNewsRequest) -> UnifiedNewsResponse:
        """
        统一处理新闻：搜索 -> 存储 -> 分析 -> 生成卡片
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        logger.info(f"开始统一新闻处理: query='{request.query}', user_id={request.user_id}")
        
        try:
            # 获取服务实例
            await self._get_services()
            
            # 1. 搜索新闻
            logger.info("步骤1: 搜索新闻")
            search_result = await self.news_service.search_news(
                query=request.query,
                num_results=request.num_results,
                language=request.language,
                country=request.country,
                time_period=request.time_period
            )
            
            if not search_result.articles:
                return UnifiedNewsResponse(
                    success=False,
                    message="未找到相关新闻",
                    query=request.query,
                    total_found=0,
                    processed_count=0,
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"找到 {len(search_result.articles)} 条新闻")
            
            # 2. 存储新闻到数据库
            stored_news = []
            storage_count = 0
            
            if request.enable_storage:
                logger.info("步骤2: 存储新闻到数据库")
                stored_news, storage_count = await self._store_news_articles(
                    search_result.articles, request.user_id
                )
                logger.info(f"成功存储 {storage_count} 条新闻")
            
            # 3. 生成AI分析摘要
            ai_summary = None
            if request.enable_analysis:
                logger.info("步骤3: 生成AI分析摘要")
                ai_summary = await self._generate_ai_summary(
                    search_result.articles, request.query
                )
            
            # 4. 生成新闻卡片
            news_cards = []
            cards_generated = 0
            
            if request.enable_cards and stored_news:
                logger.info("步骤4: 生成新闻卡片")
                news_cards, cards_generated = await self._generate_news_cards(
                    stored_news[:request.max_cards], request
                )
                logger.info(f"成功生成 {cards_generated} 张新闻卡片")
            
            # 构建响应
            processing_time = time.time() - start_time
            
            response = UnifiedNewsResponse(
                success=True,
                message=f"成功处理 {len(search_result.articles)} 条新闻",
                query=request.query,
                total_found=len(search_result.articles),
                processed_count=len(search_result.articles),
                news_articles=[article.dict() for article in search_result.articles],
                news_cards=news_cards,
                ai_summary=ai_summary,
                processing_time=processing_time,
                storage_count=storage_count,
                cards_generated=cards_generated,
                errors=errors,
                warnings=warnings
            )
            
            logger.info(f"统一新闻处理完成: 耗时 {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"统一新闻处理失败: {e}")
            return UnifiedNewsResponse(
                success=False,
                message=f"处理失败: {str(e)}",
                query=request.query,
                total_found=0,
                processed_count=0,
                processing_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def _store_news_articles(self, articles, user_id: str) -> tuple[List[NewsModel], int]:
        """存储新闻文章到MongoDB"""
        stored_news = []
        storage_count = 0
        
        try:
            db = await get_mongodb_database()
            if not db:
                logger.warning("数据库连接失败，跳过存储")
                return stored_news, 0
            
            for article in articles:
                try:
                    # 检查是否已存在
                    existing = await db[Collections.NEWS].find_one({
                        "url": article.link
                    })
                    
                    if existing:
                        # 转换为NewsModel
                        news_model = NewsModel(
                            id=str(existing["_id"]),
                            title=existing["title"],
                            content=existing.get("content", ""),
                            summary=existing.get("summary", ""),
                            url=existing["url"],
                            source=NewsSource.SERPAPI,
                            category=NewsCategory.OTHER,
                            published_at=existing.get("published_at", datetime.utcnow())
                        )
                        stored_news.append(news_model)
                        continue
                    
                    # 创建新的新闻记录
                    news_doc = {
                        "title": article.title,
                        "content": article.snippet,
                        "summary": article.snippet,
                        "url": article.link,
                        "source": NewsSource.SERPAPI.value,
                        "category": NewsCategory.OTHER.value,
                        "published_at": datetime.utcnow(),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "created_by": user_id,
                        "metadata": {
                            "serpapi_source": article.source,
                            "serpapi_position": article.position,
                            "thumbnail": article.thumbnail
                        }
                    }
                    
                    result = await db[Collections.NEWS].insert_one(news_doc)
                    
                    # 转换为NewsModel
                    news_model = NewsModel(
                        id=str(result.inserted_id),
                        title=article.title,
                        content=article.snippet,
                        summary=article.snippet,
                        url=article.link,
                        source=NewsSource.SERPAPI,
                        category=NewsCategory.OTHER,
                        published_at=datetime.utcnow()
                    )
                    
                    stored_news.append(news_model)
                    storage_count += 1
                    
                except Exception as e:
                    logger.warning(f"存储单条新闻失败: {e}")
                    continue
            
            return stored_news, storage_count
            
        except Exception as e:
            logger.error(f"存储新闻失败: {e}")
            return stored_news, 0
    
    async def _generate_ai_summary(self, articles, query: str) -> Optional[str]:
        """生成AI分析摘要"""
        try:
            # 构建新闻内容
            news_content = "\n\n".join([
                f"标题: {article.title}\n内容: {article.snippet}"
                for article in articles[:5]  # 只取前5条
            ])
            
            prompt = f"""
基于以下搜索查询和新闻内容，请生成一个综合分析摘要：

搜索查询: {query}

新闻内容:
{news_content}

请提供：
1. 主要事件概述
2. 关键趋势分析
3. 重要观点总结
4. 影响评估

请用中文回答，控制在300字以内。
"""
            
            response = await self.qwen_service.chat(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"生成AI摘要失败: {e}")
            return None
    
    async def _generate_news_cards(self, news_list: List[NewsModel], request: UnifiedNewsRequest) -> tuple[List[Dict], int]:
        """生成新闻卡片"""
        cards = []
        cards_generated = 0
        
        try:
            for news in news_list:
                try:
                    card_request = NewsCardRequest(
                        news_id=news.id,
                        include_sentiment=request.include_sentiment,
                        include_summary=request.include_summary,
                        include_entities=True,
                        max_summary_length=200
                    )
                    
                    card_response = await self.card_service.generate_card(card_request)
                    
                    if card_response and card_response.card:
                        cards.append(card_response.card.dict())
                        cards_generated += 1
                    
                except Exception as e:
                    logger.warning(f"生成新闻卡片失败 {news.id}: {e}")
                    continue
            
            return cards, cards_generated
            
        except Exception as e:
            logger.error(f"批量生成新闻卡片失败: {e}")
            return cards, 0


# 服务实例
_unified_news_service = None

async def get_unified_news_service() -> UnifiedNewsService:
    """获取统一新闻服务实例"""
    global _unified_news_service
    if _unified_news_service is None:
        _unified_news_service = UnifiedNewsService()
    return _unified_news_service
