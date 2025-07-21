#!/usr/bin/env python3
"""
调试存储的新闻数据结构
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple_storage():
    """测试简单的新闻存储"""
    print("🔍 测试简单的新闻存储...")
    
    # 只启用搜索和存储
    test_data = {
        "query": "科技",
        "num_results": 2,
        "enable_storage": True,
        "enable_vectorization": False,
        "enable_ai_analysis": False,
        "enable_card_generation": False,
        "enable_sentiment_analysis": False,
        "enable_user_memory": False,
        "max_cards": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 存储测试成功")
            print(f"找到新闻: {result.get('total_found', 0)}")
            print(f"处理数量: {result.get('processed_count', 0)}")
            
            # 检查新闻文章结构
            news_articles = result.get('news_articles', [])
            print(f"\n📰 新闻文章数量: {len(news_articles)}")
            
            if news_articles:
                first_article = news_articles[0]
                print(f"\n第一篇新闻结构:")
                print(f"  - _id: {first_article.get('_id', 'N/A')}")
                print(f"  - title: {first_article.get('title', 'N/A')}")
                print(f"  - url: {first_article.get('url', 'N/A')}")
                print(f"  - source: {first_article.get('source', 'N/A')}")
                print(f"  - created_by: {first_article.get('created_by', 'N/A')}")
                
                # 打印完整结构
                print(f"\n完整结构: {json.dumps(first_article, indent=2, ensure_ascii=False)}")
                
                # 测试直接卡片生成
                news_id = first_article.get('_id')
                if news_id:
                    print(f"\n🎴 测试直接卡片生成 (ID: {news_id})")
                    test_direct_card_generation(news_id)
            
        else:
            print(f"❌ 存储测试失败: {response.status_code}")
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"💥 异常: {e}")

def test_direct_card_generation(news_id):
    """直接测试卡片生成"""
    try:
        card_data = {
            "news_id": news_id,
            "include_sentiment": False,
            "include_entities": False,
            "include_related": False,
            "max_summary_length": 100
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/news-cards/generate",
            json=card_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 直接卡片生成成功")
            card = result.get('card', {})
            print(f"  - 卡片标题: {card.get('title', 'N/A')}")
            print(f"  - 卡片ID: {card.get('metadata', {}).get('card_id', 'N/A')}")
        else:
            print(f"  ❌ 直接卡片生成失败: {response.status_code}")
            print(f"  错误: {response.text}")
            
    except Exception as e:
        print(f"  💥 直接卡片生成异常: {e}")

if __name__ == "__main__":
    test_simple_storage()
