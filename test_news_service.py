
import asyncio
import sys
sys.path.append("backend")

from services.news_service import NewsService

async def test():
    news_service = NewsService()
    news_id = "0984dcd9-b0ac-4381-ac15-842c827d9780"
    
    try:
        news = await news_service.get_news_by_id(news_id)
        if news:
            print(f"✅ 找到新闻: {news.title}")
            print(f"新闻ID: {news.id}")
            print(f"新闻URL: {news.url}")
            print(f"新闻来源: {news.source}")
        else:
            print(f"❌ 未找到新闻: {news_id}")
    except Exception as e:
        print(f"💥 异常: {e}")

asyncio.run(test())
