"""
新闻搜索和入库服务 - 带去重和刷新机制
基于关键词搜索新闻并保存到数据库，支持关键词丰富和定期刷新
设计为智能体工具调用的接口
"""
import asyncio
import hashlib
import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from langchain_community.utilities import SerpAPIWrapper

from core.config import settings
from core.database import get_mongodb_database, Collections

logger = logging.getLogger(__name__)


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
    updated_count: int  # 更新的新闻数量（关键词丰富）
    search_time: float
    timestamp: datetime
    news_ids: List[str]
    updated_ids: List[str] = []  # 更新的新闻ID列表
    status: str = "success"
    message: str = ""


class NewsRefreshResult(BaseModel):
    """新闻刷新结果模型"""
    cleaned_count: int  # 清理的过期新闻数量
    refreshed_keywords: List[str]  # 重新搜索的关键词
    new_articles_count: int  # 新搜索到的文章数量
    refresh_time: float
    timestamp: datetime
    status: str = "success"
    message: str = ""


class NewsDocument(BaseModel):
    """新闻文档模型（对应数据库结构）"""
    _id: str
    session_id: str  # 会话ID
    title: str  # 新闻标题
    date: str  # 新闻发布日期（YYYY-MM-DD格式，用于过期判断）
    category: Optional[str] = None  # 新闻分类（暂时为空）
    keywords: List[str]  # 关键词列表，会不断丰富
    url: str  # 新闻链接
    source: str  # 新闻来源
    content: str  # 新闻全文内容
    is_embedded: bool = False  # 是否已经向量嵌入
    sentiment: Optional[str] = None  # 情感分析结果（暂时为空）
    expire_days: int = Field(default=3, description="过期天数，默认3天")


class SmartNewsService:
    """
    智能新闻搜索和管理服务
    
    核心功能：
    1. 智能去重 - 基于标题和URL字符串比较去重
    2. 关键词丰富 - 相同新闻的关键词会自动合并
    3. 定期刷新 - 清理过期新闻并重新搜索关键词
    4. 智能体友好 - 设计为工具调用接口
    """
    
    def __init__(self):
        """初始化智能新闻服务"""
        self.serpapi_key = settings.SERPAPI_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # 设置SerpAPI环境变量
        os.environ["SERPAPI_API_KEY"] = self.serpapi_key or ""
        
        # 配置SerpAPI参数
        self.serp_params = {
            "engine": "google",
            "tbm": "nws",  # 搜索新闻
            "gl": "cn",    # 地理位置
            "hl": "zh-cn", # 界面语言
        }
        
        logger.info(f"智能新闻服务初始化完成，API密钥状态: {'已配置' if self.serpapi_key else '未配置'}")
        
    async def search_and_save_with_dedup(self, request: NewsSearchRequest) -> NewsSearchResult:
        """
        智能搜索新闻并保存，支持去重和关键词丰富
        
        去重逻辑：
        1. 直接使用标题和URL字符串比较检查重复
        2. 如果新闻已存在（相同标题和URL），将新关键词合并到现有关键词中
        3. 如果新闻不存在，创建新记录
        4. 搜索前自动清理该会话的过期新闻
        
        Args:
            request: 搜索请求参数
            
        Returns:
            NewsSearchResult: 搜索和处理结果
        """
        start_time = datetime.now()
        query = " ".join(request.keywords)
        
        logger.info(f"开始智能搜索新闻 [会话: {request.session_id}]: {query}")
        
        try:
            # 检查API密钥
            if not self.serpapi_key:
                return NewsSearchResult(
                    query=query,
                    total_found=0,
                    saved_count=0,
                    updated_count=0,
                    search_time=0.0,
                    timestamp=datetime.now(),
                    news_ids=[],
                    status="error",
                    message="SerpAPI密钥未配置"
                )
            
            # 搜索前先自动清理该会话的过期新闻
            await self._auto_cleanup_expired_news(request.session_id)
            
            # 使用SerpAPI搜索新闻
            articles = await self._search_with_serpapi(request)
            
            # 智能保存到数据库（支持去重和关键词丰富）
            save_result = await self._smart_save_articles(articles, request.keywords, request.session_id)
            
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
                message=f"搜索失败: {str(e)}"
            )
    
    async def refresh_expired_news(self, session_id: str, expire_days: int = 3) -> NewsRefreshResult:
        """
        刷新指定会话的过期新闻
        
        刷新逻辑：
        1. 查找指定会话超过指定天数的新闻
        2. 收集这些新闻的关键词
        3. 删除过期新闻
        4. 用收集的关键词重新搜索最新新闻
        
        Args:
            session_id: 会话ID
            expire_days: 过期天数，默认3天
            
        Returns:
            NewsRefreshResult: 刷新结果
        """
        start_time = datetime.now()
        
        logger.info(f"开始刷新过期新闻 [会话: {session_id}]，过期标准: {expire_days} 天")
        
        try:
            db = await get_mongodb_database()
            if db is None:
                return NewsRefreshResult(
                    cleaned_count=0,
                    refreshed_keywords=[],
                    new_articles_count=0,
                    refresh_time=0.0,
                    timestamp=datetime.now(),
                    status="error",
                    message="数据库连接失败"
                )
            
            news_collection = db[Collections.NEWS]
            
            # 计算过期日期（当前日期 - 过期天数）
            expire_date = (datetime.now() - timedelta(days=expire_days)).strftime("%Y-%m-%d")
            
            # 查找指定会话的过期新闻并收集关键词
            expired_query = {
                "session_id": session_id,
                "date": {"$lt": expire_date}
            }
            expired_news = []
            all_keywords = set()
            
            async for doc in news_collection.find(expired_query):
                expired_news.append(doc)
                all_keywords.update(doc.get("keywords", []))
            
            cleaned_count = len(expired_news)
            logger.info(f"找到 {cleaned_count} 篇过期新闻，收集到 {len(all_keywords)} 个关键词")
            
            # 删除过期新闻
            if cleaned_count > 0:
                delete_result = await news_collection.delete_many(expired_query)
                logger.info(f"删除了 {delete_result.deleted_count} 篇过期新闻")
            
            # 用收集的关键词重新搜索
            new_articles_count = 0
            refreshed_keywords = list(all_keywords)
            
            if all_keywords and self.serpapi_key:
                # 分批搜索关键词（每次最多5个关键词）
                keyword_batches = [list(all_keywords)[i:i+5] for i in range(0, len(all_keywords), 5)]
                
                for batch in keyword_batches[:3]:  # 最多处理3批，避免API配额超限
                    try:
                        request = NewsSearchRequest(
                            session_id=session_id,
                            keywords=batch,
                            num_results=5,  # 每批少量搜索
                            time_period="1d"
                        )
                        
                        result = await self.search_and_save_with_dedup(request)
                        if result.status == "success":
                            new_articles_count += result.saved_count
                            
                    except Exception as e:
                        logger.warning(f"刷新关键词 {batch} 失败: {str(e)}")
                        continue
            
            refresh_time = (datetime.now() - start_time).total_seconds()
            
            result = NewsRefreshResult(
                cleaned_count=cleaned_count,
                refreshed_keywords=refreshed_keywords,
                new_articles_count=new_articles_count,
                refresh_time=refresh_time,
                timestamp=datetime.now(),
                status="success",
                message=f"清理 {cleaned_count} 篇过期新闻，重新搜索 {len(refreshed_keywords)} 个关键词，新增 {new_articles_count} 篇新闻"
            )
            
            logger.info(f"新闻刷新完成 [会话: {session_id}]: {result.message}")
            return result
            
        except Exception as e:
            logger.error(f"新闻刷新失败 [会话: {session_id}]: {str(e)}")
            refresh_time = (datetime.now() - start_time).total_seconds()
            return NewsRefreshResult(
                cleaned_count=0,
                refreshed_keywords=[],
                new_articles_count=0,
                refresh_time=refresh_time,
                timestamp=datetime.now(),
                status="error",
                message=f"刷新失败: {str(e)}"
            )
    
    async def _search_with_serpapi(self, request: NewsSearchRequest) -> List[Dict[str, Any]]:
        """使用SerpAPI搜索Google新闻"""
        try:
            query = " ".join(request.keywords)
            
            # 更新搜索参数
            search_params = self.serp_params.copy()
            search_params.update({
                "q": query,
                "num": min(request.num_results, 50),
                "hl": request.language,
                "gl": request.country
            })
            
            # 添加时间过滤
            if request.time_period:
                time_mapping = {
                    "1d": "d", "1w": "w", "1m": "m", "1y": "y"
                }
                if request.time_period in time_mapping:
                    search_params["tbs"] = f"qdr:{time_mapping[request.time_period]}"
            
            # 使用SerpAPIWrapper进行搜索
            search = SerpAPIWrapper(params=search_params)
            
            # 异步执行搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, search.run, query)
            
            # 解析搜索结果
            articles = self._parse_serp_results(results, query)
            
            logger.info(f"SerpAPI 搜索到 {len(articles)} 篇新闻")
            return articles
            
        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {str(e)}")
            return []
    
    def _parse_serp_results(self, results, query: str) -> List[Dict[str, Any]]:
        """解析SerpAPI返回的搜索结果"""
        articles = []
        
        try:
            # 处理不同类型的结果
            if isinstance(results, str):
                # 字符串格式解析
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
                    
            elif isinstance(results, list):
                # 列表格式处理
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
                            
            elif isinstance(results, dict):
                # 字典格式处理
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
            
            # 确保所有文章都有必要字段
            processed_articles = []
            for article in articles:
                if article.get('title') and article.get('url'):
                    processed_article = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', 'Unknown'),
                        'snippet': article.get('snippet', ''),
                        'date': article.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'origin': 'serpapi'
                    }
                    processed_articles.append(processed_article)
            
            return processed_articles
            
        except Exception as e:
            logger.error(f"解析搜索结果失败: {str(e)}")
            logger.error(f"结果类型: {type(results)}")
            return []
    
    async def _auto_cleanup_expired_news(self, session_id: str, expire_days: int = 3):
        """
        自动清理指定会话的过期新闻（仅删除，不重新搜索）
        
        Args:
            session_id: 会话ID
            expire_days: 过期天数，默认3天
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.warning("数据库连接失败，跳过自动清理")
                return
            
            news_collection = db[Collections.NEWS]
            
            # 计算过期日期（当前日期 - 过期天数）
            expire_date = (datetime.now() - timedelta(days=expire_days)).strftime("%Y-%m-%d")
            
            # 删除指定会话的过期新闻（新闻日期早于过期日期）
            expired_query = {
                "session_id": session_id,
                "date": {"$lt": expire_date}
            }
            
            delete_result = await news_collection.delete_many(expired_query)
            
            if delete_result.deleted_count > 0:
                logger.info(f"自动清理过期新闻 [会话: {session_id}]: 删除了 {delete_result.deleted_count} 篇过期新闻（日期早于 {expire_date}）")
            
        except Exception as e:
            logger.warning(f"自动清理过期新闻失败 [会话: {session_id}]: {str(e)}")
    
    async def _smart_save_articles(self, articles: List[Dict[str, Any]], keywords: List[str], session_id: str) -> Dict[str, Any]:
        """
        智能保存文章，支持去重和关键词丰富
        
        核心逻辑：
        1. 直接使用标题和URL字符串比较查找重复文章
        2. 如果文章已存在（相同标题和URL），合并关键词
        3. 如果文章不存在，创建新记录
        
        Args:
            articles: 文章列表
            keywords: 关键词列表
            session_id: 会话ID
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                logger.error("数据库连接失败")
                return {"saved_count": 0, "updated_count": 0, "saved_ids": [], "updated_ids": []}
                
            news_collection = db[Collections.NEWS]
            saved_ids = []
            updated_ids = []
            saved_count = 0
            updated_count = 0
            
            for article in articles:
                try:
                    # 清理标题和URL用于比较
                    clean_title = re.sub(r'\s+', ' ', article["title"].strip())
                    clean_url = article["url"].strip()
                    
                    # 先检查是否重复，无论是否能获取到内容
                    existing_doc = await news_collection.find_one({
                        "session_id": session_id,
                        "title": clean_title,
                        "url": clean_url
                    })
                    
                    # 获取新闻全文内容（对于重复新闻，不需要重新获取内容）
                    content = ""
                    if not existing_doc:
                        content = await self._fetch_article_content(article["url"])
                        if not content:
                            logger.warning(f"无法获取文章内容，跳过新文章: {article['title']}")
                            continue
                    
                    if existing_doc:
                        # 文章已存在，丰富关键词
                        existing_keywords = set(existing_doc.get("keywords", []))
                        new_keywords = set(keywords)
                        
                        # 调试日志：显示关键词比较过程
                        logger.info(f"发现重复新闻: {clean_title[:50]}...")
                        logger.info(f"  现有关键词: {list(existing_keywords)}")
                        logger.info(f"  搜索关键词: {list(new_keywords)}")
                        logger.info(f"  是否完全包含: {new_keywords.issubset(existing_keywords)}")
                        
                        # 如果有新关键词，则更新
                        if not new_keywords.issubset(existing_keywords):
                            merged_keywords = list(existing_keywords.union(new_keywords))
                            
                            logger.info(f"  合并后关键词: {merged_keywords}")
                            
                            update_result = await news_collection.update_one(
                                {"_id": existing_doc["_id"]},
                                {"$set": {"keywords": merged_keywords}}
                            )
                            
                            logger.info(f"  数据库更新结果: matched={update_result.matched_count}, modified={update_result.modified_count}")
                            
                            if update_result.modified_count > 0:
                                updated_ids.append(str(existing_doc["_id"]))
                                updated_count += 1
                                logger.info(f"✅ 成功更新新闻关键词: {clean_title[:50]}...")
                                logger.info(f"  原关键词: {list(existing_keywords)}")
                                logger.info(f"  新关键词: {merged_keywords}")
                            else:
                                logger.warning(f"⚠️ 数据库更新失败或无变化: {clean_title[:50]}...")
                        else:
                            logger.info(f"新闻关键词无变化，跳过重复新闻: {clean_title[:50]}...")
                    
                    else:
                        # 文章不存在，创建新记录
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
                        saved_ids.append(doc_id)
                        saved_count += 1
                        
                        logger.info(f"保存新新闻: {clean_title[:50]}...")
                        logger.info(f"  关键词: {keywords}")
                        logger.info(f"  URL: {clean_url[:80]}...")
                    
                except Exception as e:
                    logger.error(f"处理新闻失败 [{article.get('title', 'Unknown')[:50]}...]: {str(e)}")
                    continue
            
            return {
                "saved_count": saved_count,
                "updated_count": updated_count,
                "saved_ids": saved_ids,
                "updated_ids": updated_ids
            }
            
        except Exception as e:
            logger.error(f"智能保存失败: {str(e)}")
            return {"saved_count": 0, "updated_count": 0, "saved_ids": [], "updated_ids": []}
    
    async def _fetch_article_content(self, url: str) -> str:
        """获取新闻文章全文内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await self.client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除不需要的标签
            for script in soup(["script", "style", "nav", "header", "footer", "aside", "ad"]):
                script.decompose()
            
            # 尝试多种方式提取正文内容
            content = ""
            content_selectors = [
                'article', '.article-content', '.article-body', '.post-content', 
                '.entry-content', '.content', '.main-content', '.story-content', 
                '.news-content', '[itemprop="articleBody"]', 'main', '[role="main"]'
            ]
            
            for selector in content_selectors:
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
            
            # 清理文本
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】]', '', content)
            content = content.strip()
            
            # 限制内容长度
            if len(content) > 20000:
                content = content[:20000] + "..."
            
            return content
            
        except Exception as e:
            logger.warning(f"获取文章内容失败 [{url}]: {str(e)}")
            return ""
    
    def _generate_news_id(self, title: str, url: str, session_id: str) -> str:
        """生成新闻唯一ID：hash(title + url + session_id)"""
        # 清理标题和URL中的特殊字符，确保一致性
        clean_title = re.sub(r'\s+', ' ', title.strip())
        clean_url = url.strip()
        content = f"{clean_title}_{clean_url}_{session_id}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式为YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
            
        try:
            # 处理相对时间
            date_str = date_str.strip().lower()
            
            if any(x in date_str for x in ['小时前', 'hours ago', 'hour ago', '分钟前', 'minutes ago', 'minute ago', '天前', 'days ago', 'day ago', '周前', 'weeks ago', 'week ago', 'ago', '前']):
                return datetime.now().strftime("%Y-%m-%d")
            
            # 尝试解析标准日期格式
            date_formats = [
                "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
                "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"
            ]
            
            for fmt in date_formats:
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
    
    async def close(self):
        """关闭服务，清理资源"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
        logger.info("智能新闻服务已关闭")


# ===============================
# 智能体工具调用接口
# ===============================

# 全局服务实例
_smart_news_service: Optional[SmartNewsService] = None


async def get_smart_news_service() -> SmartNewsService:
    """获取智能新闻服务实例（单例模式）"""
    global _smart_news_service
    if _smart_news_service is None:
        _smart_news_service = SmartNewsService()
    return _smart_news_service


async def smart_search_news(
    session_id: str,
    keywords: List[str],
    num_results: int = 10,
    language: str = "zh-cn",
    country: str = "cn",
    time_period: str = "1d"
) -> NewsSearchResult:
    """
    智能搜索新闻并入库（智能体工具调用接口）
    
    核心特性：
    - 智能去重：基于标题和URL字符串直接比较去重
    - 关键词丰富：相同新闻的关键词会自动合并
    - 结构化存储：统一的数据库结构
    - 自动清理：搜索前自动清理该会话的过期新闻
    
    Args:
        session_id: 会话ID
        keywords: 搜索关键词列表
        num_results: 搜索结果数量，默认10，最大50
        language: 搜索语言，默认zh-cn
        country: 搜索地区，默认cn
        time_period: 时间范围，默认1d（1天），可选1w（1周）、1m（1月）
        
    Returns:
        NewsSearchResult: 搜索和入库结果
    """
    try:
        # 参数验证和修正
        if not session_id:
            return NewsSearchResult(
                query="",
                total_found=0,
                saved_count=0,
                updated_count=0,
                search_time=0.0,
                timestamp=datetime.now(),
                news_ids=[],
                status="error",
                message="会话ID不能为空"
            )
            
        if not keywords:
            return NewsSearchResult(
                query="",
                total_found=0,
                saved_count=0,
                updated_count=0,
                search_time=0.0,
                timestamp=datetime.now(),
                news_ids=[],
                status="error",
                message="关键词列表不能为空"
            )
        
        # 限制搜索结果数量
        if num_results <= 0:
            num_results = 1
        elif num_results > 50:
            num_results = 50
            
        service = await get_smart_news_service()
        request = NewsSearchRequest(
            session_id=session_id,
            keywords=keywords,
            num_results=num_results,
            language=language,
            country=country,
            time_period=time_period
        )
        return await service.search_and_save_with_dedup(request)
        
    except Exception as e:
        logger.error(f"智能体调用接口错误: {str(e)}")
        return NewsSearchResult(
            query=" ".join(keywords) if keywords else "",
            total_found=0,
            saved_count=0,
            updated_count=0,
            search_time=0.0,
            timestamp=datetime.now(),
            news_ids=[],
            status="error",
            message=f"调用失败: {str(e)}"
        )


async def refresh_news_database(session_id: str, expire_days: int = 3) -> NewsRefreshResult:
    """
    刷新指定会话的新闻数据库（智能体工具调用接口）
    
    刷新逻辑：
    1. 查找并删除指定会话超过指定天数的新闻
    2. 收集删除新闻的关键词
    3. 用这些关键词重新搜索最新新闻
    
    Args:
        session_id: 会话ID
        expire_days: 过期天数，默认3天
        
    Returns:
        NewsRefreshResult: 刷新结果
    """
    if not session_id:
        return NewsRefreshResult(
            cleaned_count=0,
            refreshed_keywords=[],
            new_articles_count=0,
            refresh_time=0.0,
            timestamp=datetime.now(),
            status="error",
            message="会话ID不能为空"
        )
        
    service = await get_smart_news_service()
    return await service.refresh_expired_news(session_id, expire_days)


async def get_news_statistics(session_id: str = None) -> Dict[str, Any]:
    """
    获取新闻数据库统计信息（智能体工具调用接口）
    
    Args:
        session_id: 会话ID，如果提供则只统计该会话的新闻，否则统计所有新闻
    
    Returns:
        Dict: 包含总数、热门关键词、最新更新时间等统计信息
    """
    try:
        db = await get_mongodb_database()
        if db is None:
            return {"error": "数据库连接失败"}
        
        news_collection = db[Collections.NEWS]
        
        # 构建查询条件
        query_filter = {}
        if session_id:
            query_filter["session_id"] = session_id
        
        # 总新闻数
        total_count = await news_collection.count_documents(query_filter)
        
        # 最新更新时间（改为按日期排序）
        latest_news = await news_collection.find_one(query_filter, sort=[("date", -1)])
        latest_date = latest_news["date"] if latest_news else None
        
        # 热门关键词统计
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
        
        # 按日期统计
        today = datetime.now().strftime("%Y-%m-%d")
        today_filter = query_filter.copy()
        today_filter["date"] = today
        today_count = await news_collection.count_documents(today_filter)
        
        return {
            "session_id": session_id,
            "total_count": total_count,
            "today_count": today_count,
            "latest_date": latest_date,
            "top_keywords": top_keywords,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"获取新闻统计失败: {str(e)}")
        return {"error": f"获取统计信息失败: {str(e)}"}
        

async def get_session_news_list(session_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    获取指定会话的新闻列表（智能体工具调用接口）
    
    Args:
        session_id: 会话ID
        limit: 返回数量限制，默认20
        offset: 偏移量，默认0
        
    Returns:
        Dict: 包含新闻列表和统计信息
    """
    try:
        if not session_id:
            return {"error": "会话ID不能为空"}
            
        db = await get_mongodb_database()
        if db is None:
            return {"error": "数据库连接失败"}
        
        news_collection = db[Collections.NEWS]
        
        # 查询条件
        query_filter = {"session_id": session_id}
        
        # 获取新闻列表（按日期排序）
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
        
        # 统计信息
        total_count = await news_collection.count_documents(query_filter)
        
        return {
            "session_id": session_id,
            "news_list": news_list,
            "total_count": total_count,
            "returned_count": len(news_list),
            "offset": offset,
            "limit": limit,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"获取会话新闻列表失败: {str(e)}")
        return {"error": f"获取新闻列表失败: {str(e)}"}
