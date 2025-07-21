#!/usr/bin/env python3
"""
调试新闻卡片生成
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_card_generation_directly():
    """直接测试新闻卡片生成"""
    print("🔍 直接测试新闻卡片生成...")
    
    # 使用一个已知存在的新闻ID（从上面的输出中获取）
    news_id = "0984dcd9-b0ac-4381-ac15-842c827d9780"  # 香港人工智能产业发展
    
    test_data = {
        "news_id": news_id,
        "include_sentiment": True,
        "include_entities": True,
        "include_related": True,
        "max_summary_length": 200
    }
    
    try:
        print(f"📤 测试卡片生成请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/news-cards/generate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 卡片生成成功")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 卡片生成失败")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"💥 异常: {e}")

def test_news_service_get_by_id():
    """测试新闻服务的get_by_id方法"""
    print("\n🔍 测试新闻服务...")
    
    # 创建一个简单的测试脚本
    test_script = '''
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
'''
    
    with open("test_news_service.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("📝 已创建测试脚本 test_news_service.py")

if __name__ == "__main__":
    test_card_generation_directly()
    test_news_service_get_by_id()
