#!/usr/bin/env python3
"""
调试流水线中的卡片生成问题
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_pipeline_with_detailed_logging():
    """测试流水线并获取详细日志"""
    print("🔍 测试流水线卡片生成...")
    
    # 最简单的请求，只启用卡片生成
    test_data = {
        "query": "人工智能",
        "num_results": 2,  # 减少数量
        "enable_storage": True,
        "enable_vectorization": False,
        "enable_ai_analysis": False,
        "enable_card_generation": True,  # 只启用卡片生成
        "enable_sentiment_analysis": False,
        "enable_user_memory": False,
        "max_cards": 2
    }
    
    try:
        print(f"📤 发送请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📥 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            
            # 详细分析结果
            print(f"\n📊 处理结果:")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            
            # 检查阶段结果
            stage_results = result.get('stage_results', [])
            print(f"\n📋 阶段结果:")
            for i, stage in enumerate(stage_results):
                stage_name = stage.get('stage', f'阶段{i+1}')
                success = stage.get('success', False)
                error = stage.get('error', '')
                print(f"  {i+1}. {stage_name}: {'✅' if success else '❌'}")
                if not success and error:
                    print(f"     错误: {error}")
            
            # 检查错误和警告
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            if errors:
                print(f"\n❌ 错误:")
                for error in errors:
                    print(f"  - {error}")
            if warnings:
                print(f"\n⚠️ 警告:")
                for warning in warnings:
                    print(f"  - {warning}")
            
            # 检查新闻文章
            news_articles = result.get('news_articles', [])
            print(f"\n📰 新闻文章数量: {len(news_articles)}")
            if news_articles:
                print(f"  第一篇新闻ID: {news_articles[0].get('_id', 'N/A')}")
                print(f"  第一篇新闻标题: {news_articles[0].get('title', 'N/A')}")
            
            # 检查新闻卡片
            news_cards = result.get('news_cards', [])
            print(f"\n🎴 新闻卡片数量: {len(news_cards)}")
            if news_cards:
                print(f"  第一张卡片: {json.dumps(news_cards[0], indent=2, ensure_ascii=False)}")
            else:
                print("  没有生成任何卡片")
                
        else:
            print(f"❌ 请求失败")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"💥 异常: {e}")

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 服务器健康检查通过")
        else:
            print(f"❌ 服务器健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"💥 服务器连接异常: {e}")

if __name__ == "__main__":
    test_database_connection()
    test_pipeline_with_detailed_logging()
