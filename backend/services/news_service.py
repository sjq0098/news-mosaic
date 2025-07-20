"""
新闻搜索服务 - 使用 SerpAPI
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class NewsArticle(BaseModel):
    """新闻文章模型"""
    title: str
    snippet: str
    link: str
    source: str
    date: Optional[str] = None
    thumbnail: Optional[str] = None
    position: Optional[int] = None


class NewsSearchResult(BaseModel):
    """新闻搜索结果模型"""
    query: str
    articles: List[NewsArticle]
    total_results: int
    search_time: float
    timestamp: datetime


class NewsService:
    """新闻搜索服务"""
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_news(
        self,
        query: str,
        num_results: int = 10,
        language: str = "zh-cn",
        country: str = "cn",
        time_period: str = "1d"  # 1d, 1w, 1m, 1y
    ) -> NewsSearchResult:
        """
        搜索新闻
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            language: 语言代码
            country: 国家代码
            time_period: 时间范围
        """
        start_time = datetime.now()
        
        try:
            params = {
                "engine": "google_news",
                "q": query,
                "api_key": self.api_key,
                "hl": language,
                "gl": country,
                "num": min(num_results, 100),  # SerpAPI 限制
                "tbm": "nws"  # 新闻搜索
            }
            
            # 添加时间范围
            if time_period:
                params["tbs"] = f"qdr:{time_period}"
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = self._parse_news_results(data)
            
            search_time = (datetime.now() - start_time).total_seconds()
            
            return NewsSearchResult(
                query=query,
                articles=articles,
                total_results=len(articles),
                search_time=search_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"新闻搜索失败: {str(e)}")
            raise
    
    def _parse_news_results(self, data: Dict[str, Any]) -> List[NewsArticle]:
        """解析 SerpAPI 返回的新闻结果"""
        articles = []
        
        if "news_results" in data:
            for idx, item in enumerate(data["news_results"]):
                try:
                    # 处理source字段，可能是字符串或字典
                    source_data = item.get("source", "")
                    if isinstance(source_data, dict):
                        source = source_data.get("name", "")
                    else:
                        source = str(source_data)
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        link=item.get("link", ""),
                        source=source,
                        date=item.get("date", ""),
                        thumbnail=item.get("thumbnail"),
                        position=idx + 1
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"解析新闻文章失败: {str(e)}")
                    continue
        
        return articles
    
    async def search_trending_news(
        self,
        language: str = "zh-cn",
        country: str = "cn",
        num_results: int = 20
    ) -> NewsSearchResult:
        """获取热门新闻"""
        return await self.search_news(
            query="热点新闻",
            num_results=num_results,
            language=language,
            country=country,
            time_period="1d"
        )
    
    async def search_news_by_category(
        self,
        category: str,
        num_results: int = 10,
        language: str = "zh-cn",
        country: str = "cn"
    ) -> NewsSearchResult:
        """
        按分类搜索新闻
        
        Args:
            category: 新闻分类 (科技、体育、财经、娱乐等)
        """
        # 构建分类查询
        category_queries = {
            "科技": "科技 技术 AI 人工智能",
            "体育": "体育 运动 足球 篮球",
            "财经": "财经 经济 股市 金融",
            "娱乐": "娱乐 明星 电影 音乐",
            "政治": "政治 政府 政策",
            "健康": "健康 医疗 养生",
            "教育": "教育 学校 大学",
            "国际": "国际 全球 世界"
        }
        
        query = category_queries.get(category, category)
        
        return await self.search_news(
            query=query,
            num_results=num_results,
            language=language,
            country=country,
            time_period="1d"
        )
    
    async def search_news_with_sentiment(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """搜索新闻并进行情感分析"""
        news_result = await self.search_news(query, num_results)
        
        # 这里可以集成情感分析服务
        # 暂时返回基础结果
        return {
            "news": news_result,
            "sentiment_summary": {
                "positive": 0,
                "negative": 0,
                "neutral": len(news_result.articles)
            }
        }
    
    async def get_news_summary(
        self,
        query: str,
        num_articles: int = 5
    ) -> Dict[str, Any]:
        """获取新闻摘要"""
        news_result = await self.search_news(query, num_articles)
        
        # 提取关键信息
        summary = {
            "query": query,
            "total_articles": len(news_result.articles),
            "sources": list(set([article.source for article in news_result.articles])),
            "key_headlines": [article.title for article in news_result.articles[:3]],
            "search_time": news_result.search_time,
            "timestamp": news_result.timestamp
        }
        
        return summary
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()


# 全局实例
news_service = NewsService()


async def get_news_service() -> NewsService:
    """获取新闻服务实例"""
    return news_service