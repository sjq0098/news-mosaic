"""
新闻搜索和管理服务 - 优化重构版
基于关键词搜索新闻并保存到数据库，支持智能去重、关键词丰富和自动刷新
"""

import asyncio
import hashlib
import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from langchain_community.utilities import SerpAPIWrapper

from core.config import settings
from core.database import get_mongodb_database, Collections
from models.news import (
    NewsSearchRequest, NewsSearchResult, NewsRefreshResult, 
    NewsDocument, NewsStatistics, NewsListResponse
)

logger = logging.getLogger(__name__)


class NewsService:
    """
    新闻搜索和管理服务
    
    核心功能：
    1. 智能去重 - 基于标题和URL字符串比较去重
    2. 关键词丰富 - 相同新闻的关键词会自动合并
    3. 自动清理 - 清理过期新闻
    4. 内容抓取 - 获取新闻全文内容
    5. 统计分析 - 提供新闻统计信息
    """
    
    # 类常量
    DEFAULT_EXPIRE_DAYS = 3
    MAX_CONTENT_LENGTH = 20000
    REQUEST_TIMEOUT = 30.0
    MAX_SEARCH_RESULTS = 50
    
    def __init__(self) -> None:
        """初始化新闻服务"""
        self.serpapi_key = settings.SERPAPI_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # 设置SerpAPI环境变量
        if self.serpapi_key:
            os.environ["SERPAPI_API_KEY"] = self.serpapi_key
        
        # 配置SerpAPI参数
        self.serp_params = {
            "engine": "google",
            "tbm": "nws",  # 搜索新闻
            "gl": "cn",    # 地理位置
            "hl": "zh-cn", # 界面语言
        }
        
        # 日期格式列表
        self.date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"
        ]
        
        # 相对时间关键词
        self.relative_time_keywords = [
            '小时前', 'hours ago', 'hour ago', '分钟前', 'minutes ago', 
            'minute ago', '天前', 'days ago', 'day ago', '周前', 
            'weeks ago', 'week ago', 'ago', '前'
        ]
        
        # 内容提取选择器
        self.content_selectors = [
            'article', '.article-content', '.article-body', '.post-content', 
            '.entry-content', '.content', '.main-content', '.story-content', 
            '.news-content', '[itemprop="articleBody"]', 'main', '[role="main"]'
        ]
        
        logger.info(f"新闻服务初始化完成，API密钥状态: {'已配置' if self.serpapi_key else '未配置'}")
    
    async def search_and_save_news(self, request: NewsSearchRequest) -> NewsSearchResult:
        """
        智能搜索新闻并保存，支持去重和关键词丰富
        
        Args:
            request: 搜索请求参数
            
        Returns:
            NewsSearchResult: 搜索和处理结果
        """
        start_time = datetime.now()
        query = " ".join(request.keywords)
        
        logger.info(f"开始智能搜索新闻 [会话: {request.session_id}]: {query}")
        
        try:
            # 验证参数
            validation_error = self._validate_search_request(request)
            if validation_error:
                return self._create_error_result(query, start_time, validation_error)
            
            # 搜索前自动清理过期新闻
            await self._auto_cleanup_expired_news(request.session_id)
            
            # 搜索新闻
            articles = await self._search_with_serpapi(request)
            
            # 智能保存到数据库
            save_result = await self._smart_save_articles(articles, request.keywords, request.session_id)
            
            # 计算搜索时间
            search_time = (datetime.now() - start_time).total_seconds()
            
            result = NewsSearchResult(
                query=query,
                total_found=len(articles),
                saved_count=save_result["saved_count"],
                updated_count=save_result["updated_count"],
                search_time=search_time,
                timestamp=datetime.now(),
                news_ids=save_result["saved_ids"],
                updated_ids=save_result["updated_ids"],
                status="success",
                message=f"找到 {len(articles)} 篇新闻，新增 {save_result['saved_count']} 篇，更新 {save_result['updated_count']} 篇"
            )
            
            logger.info(f"智能搜索完成 [会话: {request.session_id}]: {result.message}")
            return result
            
        except Exception as e:
            logger.error(f"智能新闻搜索失败 [会话: {request.session_id}]: {str(e)}")
            return self._create_error_result(query, start_time, f"搜索失败: {str(e)}")
    
    async def refresh_expired_news(self, session_id: str, expire_days: int = DEFAULT_EXPIRE_DAYS) -> NewsRefreshResult:
        """
        刷新指定会话的过期新闻
        
        Args:
            session_id: 会话ID
            expire_days: 过期天数，默认3天
            
        Returns:
            NewsRefreshResult: 刷新结果
        """
        start_time = datetime.now()
        
        logger.info(f"开始刷新过期新闻 [会话: {session_id}]，过期标准: {expire_days} 天")
        
        try:
            # 获取数据库连接
            db = await get_mongodb_database()
            if db is None:
                return self._create_refresh_error_result(start_time, "数据库连接失败")
            
            news_collection = db[Collections.NEWS]
            
            # 查找和删除过期新闻，收集关键词
            expired_data = await self._find_and_delete_expired_news(
                news_collection, session_id, expire_days
            )
            
            # 用收集的关键词重新搜索
            new_articles_count = 0
            if expired_data["keywords"] and self.serpapi_key:
                new_articles_count = await self._refresh_with_keywords(
                    session_id, expired_data["keywords"]
                )
            
            refresh_time = (datetime.now() - start_time).total_seconds()
            
            result = NewsRefreshResult(
                cleaned_count=expired_data["count"],
                refreshed_keywords=expired_data["keywords"],
                new_articles_count=new_articles_count,
                refresh_time=refresh_time,
                timestamp=datetime.now(),
                status="success",
                message=f"清理 {expired_data['count']} 篇过期新闻，重新搜索 {len(expired_data['keywords'])} 个关键词，新增 {new_articles_count} 篇新闻"
            )
            
            logger.info(f"新闻刷新完成 [会话: {session_id}]: {result.message}")
            return result
            
        except Exception as e:
            logger.error(f"新闻刷新失败 [会话: {session_id}]: {str(e)}")
            return self._create_refresh_error_result(start_time, f"刷新失败: {str(e)}")
    
    async def get_news_statistics(self, session_id: Optional[str] = None) -> NewsStatistics:
        """
        获取新闻统计信息
        
        Args:
            session_id: 会话ID，如果提供则只统计该会话的新闻
        
        Returns:
            NewsStatistics: 统计信息
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                return NewsStatistics(status="error")
            
            news_collection = db[Collections.NEWS]
            
            # 构建查询条件
            query_filter = {"session_id": session_id} if session_id else {}
            
            # 获取统计数据
            stats_data = await self._collect_statistics(news_collection, query_filter)
            
            return NewsStatistics(
                session_id=session_id,
                total_count=stats_data["total_count"],
                today_count=stats_data["today_count"],
                latest_date=stats_data["latest_date"],
                top_keywords=stats_data["top_keywords"],
                status="success"
            )
            
        except Exception as e:
            logger.error(f"获取新闻统计失败: {str(e)}")
            return NewsStatistics(status="error")
    
    async def get_session_news_list(self, session_id: str, limit: int = 20, offset: int = 0) -> NewsListResponse:
        """
        获取指定会话的新闻列表
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            NewsListResponse: 新闻列表响应
        """
        try:
            if not session_id:
                return NewsListResponse(
                    session_id="",
                    status="error"
                )
                
            db = await get_mongodb_database()
            if db is None:
                return NewsListResponse(
                    session_id=session_id,
                    status="error"
                )
            
            news_collection = db[Collections.NEWS]
            query_filter = {"session_id": session_id}
            
            # 获取新闻列表
            news_list = await self._fetch_news_list(news_collection, query_filter, limit, offset)
            
            # 获取总数
            total_count = await news_collection.count_documents(query_filter)
            
            return NewsListResponse(
                session_id=session_id,
                news_list=news_list,
                total_count=total_count,
                returned_count=len(news_list),
                offset=offset,
                limit=limit,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"获取会话新闻列表失败: {str(e)}")
            return NewsListResponse(
                session_id=session_id,
                status="error"
            )
    
    async def _search_with_serpapi(self, request: NewsSearchRequest) -> List[Dict[str, Any]]:
        """使用SerpAPI搜索新闻"""
        try:
            query = " ".join(request.keywords)
            
            # 构建搜索参数
            search_params = self._build_search_params(request, query)
            
            # 执行搜索
            search = SerpAPIWrapper(params=search_params)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, search.run, query)
            
            # 解析结果
            articles = self._parse_search_results(results)
            
            logger.info(f"SerpAPI 搜索到 {len(articles)} 篇新闻")
            return articles
            
        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {str(e)}")
            return []
    
    async def _smart_save_articles(self, articles: List[Dict[str, Any]], keywords: List[str], session_id: str) -> Dict[str, Any]:
        """智能保存文章，支持去重和关键词丰富"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return self._empty_save_result()
                
            news_collection = db[Collections.NEWS]
            result = {"saved_count": 0, "updated_count": 0, "saved_ids": [], "updated_ids": []}
            
            for article in articles:
                try:
                    save_data = await self._process_single_article(
                        news_collection, article, keywords, session_id
                    )
                    
                    # 合并结果
                    result["saved_count"] += save_data["saved"]
                    result["updated_count"] += save_data["updated"]
                    if save_data["id"]:
                        if save_data["saved"]:
                            result["saved_ids"].append(save_data["id"])
                        elif save_data["updated"]:
                            result["updated_ids"].append(save_data["id"])
                    
                except Exception as e:
                    logger.error(f"处理文章失败 [{article.get('title', 'Unknown')[:50]}...]: {str(e)}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"智能保存失败: {str(e)}")
            return self._empty_save_result()
    
    async def _process_single_article(self, news_collection, article: Dict[str, Any], keywords: List[str], session_id: str) -> Dict[str, Any]:
        """处理单个文章"""
        # 清理标题和URL
        clean_title = re.sub(r'\s+', ' ', article["title"].strip())
        clean_url = article["url"].strip()
        
        # 检查是否重复
        existing_doc = await news_collection.find_one({
            "session_id": session_id,
            "title": clean_title,
            "url": clean_url
        })
        
        if existing_doc:
            # 处理重复文章，丰富关键词
            return await self._update_existing_article(news_collection, existing_doc, keywords)
        else:
            # 创建新文章
            return await self._create_new_article(news_collection, article, keywords, session_id, clean_title, clean_url)
    
    async def _update_existing_article(self, news_collection, existing_doc: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """更新现有文章的关键词"""
        existing_keywords = set(existing_doc.get("keywords", []))
        new_keywords = set(keywords)
        
        if not new_keywords.issubset(existing_keywords):
            merged_keywords = list(existing_keywords.union(new_keywords))
            
            update_result = await news_collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {"keywords": merged_keywords}}
            )
            
            if update_result.modified_count > 0:
                logger.info(f"✅ 更新新闻关键词: {existing_doc['title'][:50]}...")
                return {"saved": 0, "updated": 1, "id": str(existing_doc["_id"])}
        
        return {"saved": 0, "updated": 0, "id": None}
    
    async def _create_new_article(self, news_collection, article: Dict[str, Any], keywords: List[str], session_id: str, clean_title: str, clean_url: str) -> Dict[str, Any]:
        """创建新文章"""
        # 获取文章内容
        content = await self._fetch_article_content(article["url"])
        if not content:
            logger.warning(f"无法获取文章内容，跳过: {clean_title}")
            return {"saved": 0, "updated": 0, "id": None}
        
        # 创建文档
        normalized_date = self._normalize_date(article["date"])
        doc_id = self._generate_news_id(clean_title, clean_url, session_id)
        
        news_doc = NewsDocument(
            _id=doc_id,
            session_id=session_id,
            title=clean_title,
            date=normalized_date,
            keywords=keywords,
            url=clean_url,
            source=article["source"],
            content=content,
            is_embedded=False
        )
        
        # 保存到数据库
        await news_collection.insert_one(news_doc.dict())
        
        logger.info(f"保存新新闻: {clean_title[:50]}...")
        return {"saved": 1, "updated": 0, "id": doc_id}
    
    async def _fetch_article_content(self, url: str) -> str:
        """获取新闻文章全文内容（优化版）"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await self.client.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除不需要的标签
            self._remove_unwanted_tags(soup)
            
            # 提取内容
            content = self._extract_content(soup)
            
            # 清理和限制内容长度
            return self._clean_content(content)
            
        except Exception as e:
            logger.warning(f"获取文章内容失败 [{url}]: {str(e)}")
            return ""
    
    def _validate_search_request(self, request: NewsSearchRequest) -> Optional[str]:
        """验证搜索请求参数"""
        if not self.serpapi_key:
            return "SerpAPI密钥未配置"
        if not request.session_id:
            return "会话ID不能为空"
        if not request.keywords:
            return "关键词列表不能为空"
        if request.num_results > self.MAX_SEARCH_RESULTS:
            request.num_results = self.MAX_SEARCH_RESULTS
        return None
    
    def _build_search_params(self, request: NewsSearchRequest, query: str) -> Dict[str, Any]:
        """构建搜索参数"""
        search_params = self.serp_params.copy()
        search_params.update({
            "q": query,
            "num": min(request.num_results, self.MAX_SEARCH_RESULTS),
            "hl": request.language,
            "gl": request.country
        })
        
        # 添加时间过滤
        time_mapping = {"1d": "d", "1w": "w", "1m": "m", "1y": "y"}
        if request.time_period in time_mapping:
            search_params["tbs"] = f"qdr:{time_mapping[request.time_period]}"
        
        return search_params
    
    def _parse_search_results(self, results) -> List[Dict[str, Any]]:
        """解析搜索结果（优化版）"""
        articles = []
        
        try:
            if isinstance(results, str):
                articles = self._parse_string_results(results)
            elif isinstance(results, list):
                articles = self._parse_list_results(results)
            elif isinstance(results, dict):
                articles = self._parse_dict_results(results)
            
            return self._validate_articles(articles)
            
        except Exception as e:
            logger.error(f"解析搜索结果失败: {str(e)}")
            return []
    
    def _parse_string_results(self, results: str) -> List[Dict[str, Any]]:
        """解析字符串格式的结果"""
        articles = []
        lines = results.split('\n')
        current_article = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_article:
                    articles.append(current_article)
                    current_article = {}
                continue
            
            if line.startswith('Title:'):
                current_article['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Link:'):
                current_article['url'] = line.replace('Link:', '').strip()
            elif line.startswith('Source:'):
                current_article['source'] = line.replace('Source:', '').strip()
            elif line.startswith('Date:'):
                current_article['date'] = line.replace('Date:', '').strip()
            elif line.startswith('Snippet:'):
                current_article['snippet'] = line.replace('Snippet:', '').strip()
        
        if current_article:
            articles.append(current_article)
        
        return articles
    
    def _parse_list_results(self, results: List) -> List[Dict[str, Any]]:
        """解析列表格式的结果"""
        articles = []
        for item in results:
            if isinstance(item, dict):
                article = {
                    'title': item.get('title', item.get('headline', '')),
                    'url': item.get('link', item.get('url', '')),
                    'source': item.get('source', item.get('site', 'Unknown')),
                    'snippet': item.get('snippet', item.get('summary', '')),
                    'date': item.get('date', item.get('published_date', datetime.now().strftime('%Y-%m-%d'))),
                }
                if article['title'] and article['url']:
                    articles.append(article)
        return articles
    
    def _parse_dict_results(self, results: Dict) -> List[Dict[str, Any]]:
        """解析字典格式的结果"""
        articles = []
        news_results = results.get('news_results', [])
        for item in news_results:
            article = {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'source': item.get('source', 'Unknown'),
                'snippet': item.get('snippet', ''),
                'date': item.get('date', datetime.now().strftime('%Y-%m-%d')),
            }
            if article['title'] and article['url']:
                articles.append(article)
        return articles
    
    def _validate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证文章列表"""
        valid_articles = []
        for article in articles:
            if article.get('title') and article.get('url'):
                valid_article = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', 'Unknown'),
                    'snippet': article.get('snippet', ''),
                    'date': article.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'origin': 'serpapi'
                }
                valid_articles.append(valid_article)
        return valid_articles
    
    def _remove_unwanted_tags(self, soup: BeautifulSoup):
        """移除不需要的HTML标签"""
        for script in soup(["script", "style", "nav", "header", "footer", "aside", "ad"]):
            script.decompose()
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content = ""
        
        # 尝试通过选择器提取内容
        for selector in self.content_selectors:
            elements = soup.select(selector)
            if elements:
                content = elements[0].get_text(separator=' ', strip=True)
                if len(content) > 200:
                    break
        
        # 如果没找到，提取所有段落
        if not content or len(content) < 200:
            paragraphs = soup.find_all(['p', 'div'])
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:
                    content_parts.append(text)
            content = ' '.join(content_parts)
        
        return content
    
    def _clean_content(self, content: str) -> str:
        """清理文本内容"""
        # 清理空白字符
        content = re.sub(r'\s+', ' ', content)
        # 清理特殊字符（保留中文字符）
        content = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】]', '', content)
        content = content.strip()
        
        # 限制内容长度
        if len(content) > self.MAX_CONTENT_LENGTH:
            content = content[:self.MAX_CONTENT_LENGTH] + "..."
        
        return content
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式（优化版）"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        
        try:
            date_str = date_str.strip().lower()
            
            # 处理相对时间
            if any(keyword in date_str for keyword in self.relative_time_keywords):
                return datetime.now().strftime("%Y-%m-%d")
            
            # 尝试解析标准日期格式
            for fmt in self.date_formats:
                try:
                    test_str = date_str[:len(fmt)]
                    dt = datetime.strptime(test_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # 如果都失败，返回今天的日期
            return datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            logger.warning(f"日期格式化失败: {str(e)}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def _generate_news_id(self, title: str, url: str, session_id: str) -> str:
        """生成新闻唯一ID"""
        content = f"{title}_{url}_{session_id}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def _auto_cleanup_expired_news(self, session_id: str, expire_days: int = DEFAULT_EXPIRE_DAYS):
        """自动清理过期新闻"""
        try:
            db = await get_mongodb_database()
            if db is None:
                return
            
            news_collection = db[Collections.NEWS]
            expire_date = (datetime.now() - timedelta(days=expire_days)).strftime("%Y-%m-%d")
            
            expired_query = {
                "session_id": session_id,
                "date": {"$lt": expire_date}
            }
            
            delete_result = await news_collection.delete_many(expired_query)
            
            if delete_result.deleted_count > 0:
                logger.info(f"自动清理过期新闻 [会话: {session_id}]: 删除 {delete_result.deleted_count} 篇")
            
        except Exception as e:
            logger.warning(f"自动清理过期新闻失败 [会话: {session_id}]: {str(e)}")
    
    async def _find_and_delete_expired_news(self, news_collection, session_id: str, expire_days: int) -> Dict[str, Any]:
        """查找并删除过期新闻，返回相关数据"""
        expire_date = (datetime.now() - timedelta(days=expire_days)).strftime("%Y-%m-%d")
        
        expired_query = {
            "session_id": session_id,
            "date": {"$lt": expire_date}
        }
        
        # 收集关键词
        all_keywords = set()
        expired_count = 0
        
        async for doc in news_collection.find(expired_query):
            expired_count += 1
            all_keywords.update(doc.get("keywords", []))
        
        # 删除过期新闻
        if expired_count > 0:
            await news_collection.delete_many(expired_query)
            logger.info(f"删除 {expired_count} 篇过期新闻，收集到 {len(all_keywords)} 个关键词")
        
        return {
            "count": expired_count,
            "keywords": list(all_keywords)
        }
    
    async def _refresh_with_keywords(self, session_id: str, keywords: List[str]) -> int:
        """用关键词重新搜索新闻"""
        new_articles_count = 0
        
        # 分批处理关键词
        keyword_batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
        
        for batch in keyword_batches[:3]:  # 限制批次避免API配额超限
            try:
                request = NewsSearchRequest(
                    session_id=session_id,
                    keywords=batch,
                    num_results=5,
                    time_period="1d"
                )
                
                result = await self.search_and_save_news(request)
                if result.status == "success":
                    new_articles_count += result.saved_count
                    
            except Exception as e:
                logger.warning(f"刷新关键词 {batch} 失败: {str(e)}")
                continue
        
        return new_articles_count
    
    async def _collect_statistics(self, news_collection, query_filter: Dict[str, Any]) -> Dict[str, Any]:
        """收集统计数据"""
        # 总新闻数
        total_count = await news_collection.count_documents(query_filter)
        
        # 最新更新时间
        latest_news = await news_collection.find_one(query_filter, sort=[("date", -1)])
        latest_date = latest_news["date"] if latest_news else None
        
        # 今日新闻数
        today = datetime.now().strftime("%Y-%m-%d")
        today_filter = query_filter.copy()
        today_filter["date"] = today
        today_count = await news_collection.count_documents(today_filter)
        
        # 热门关键词
        top_keywords = await self._get_top_keywords(news_collection, query_filter)
        
        return {
            "total_count": total_count,
            "today_count": today_count,
            "latest_date": latest_date,
            "top_keywords": top_keywords
        }
    
    async def _get_top_keywords(self, news_collection, query_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取热门关键词"""
        keyword_pipeline = [
            {"$match": query_filter},
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_keywords = []
        async for doc in news_collection.aggregate(keyword_pipeline):
            top_keywords.append({"keyword": doc["_id"], "count": doc["count"]})
        
        return top_keywords
    
    async def _fetch_news_list(self, news_collection, query_filter: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        """获取新闻列表"""
        news_cursor = news_collection.find(query_filter).sort("date", -1).skip(offset).limit(limit)
        news_list = []
        
        async for doc in news_cursor:
            news_item = {
                "id": doc["_id"],
                "title": doc["title"],
                "date": doc["date"],
                "source": doc["source"],
                "url": doc["url"],
                "keywords": doc["keywords"],
                "category": doc.get("category"),
                "sentiment": doc.get("sentiment"),
                "is_embedded": doc.get("is_embedded", False)
            }
            news_list.append(news_item)
        
        return news_list
    
    def _create_error_result(self, query: str, start_time: datetime, message: str) -> NewsSearchResult:
        """创建错误结果"""
        search_time = (datetime.now() - start_time).total_seconds()
        return NewsSearchResult(
            query=query,
            total_found=0,
            saved_count=0,
            updated_count=0,
            search_time=search_time,
            timestamp=datetime.now(),
            news_ids=[],
            status="error",
            message=message
        )
    
    def _create_refresh_error_result(self, start_time: datetime, message: str) -> NewsRefreshResult:
        """创建刷新错误结果"""
        refresh_time = (datetime.now() - start_time).total_seconds()
        return NewsRefreshResult(
            refresh_time=refresh_time,
            timestamp=datetime.now(),
            status="error",
            message=message
        )
    
    def _empty_save_result(self) -> Dict[str, Any]:
        """返回空的保存结果"""
        return {"saved_count": 0, "updated_count": 0, "saved_ids": [], "updated_ids": []}
    
    async def close(self):
        """关闭服务，清理资源"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
        logger.info("新闻服务已关闭")


# 全局服务实例（单例模式）
_news_service: Optional[NewsService] = None


async def get_news_service() -> NewsService:
    """获取新闻服务实例（单例模式）"""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
