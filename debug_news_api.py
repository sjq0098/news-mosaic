#!/usr/bin/env python3
"""
调试新闻处理API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_news_pipeline_simple():
    """测试简单的新闻处理"""
    print("🔍 调试新闻处理API...")
    
    # 最简单的请求
    test_data = {
        "query": "科技",
        "num_results": 3,
        "enable_storage": True,
        "enable_vectorization": False,
        "enable_ai_analysis": False,
        "enable_card_generation": False,
        "enable_sentiment_analysis": False,
        "enable_user_memory": False,
        "max_cards": 1
    }
    
    try:
        print(f"📤 发送请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 状态码: {response.status_code}")
        print(f"📝 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 请求失败")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"💥 异常: {e}")

def test_news_search_only():
    """测试纯新闻搜索"""
    print("\n🔍 测试纯新闻搜索...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news/search",
            json={"query": "科技", "num_results": 3},
            timeout=30
        )
        
        print(f"📥 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 新闻搜索成功")
            print(f"找到文章数: {len(result.get('data', {}).get('articles', []))}")
        else:
            print(f"❌ 新闻搜索失败: {response.text}")
            
    except Exception as e:
        print(f"💥 新闻搜索异常: {e}")

if __name__ == "__main__":
    test_news_search_only()
    test_news_pipeline_simple()
