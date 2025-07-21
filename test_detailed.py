#!/usr/bin/env python3
"""
详细测试API响应
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_enhanced_chat_detailed():
    """详细测试增强对话API"""
    print("=== 详细测试增强对话API ===")
    
    test_data = {
        "user_id": "test_user",
        "message": "你好，请介绍一下今天的新闻",
        "session_id": "test_session_123",
        "max_context_news": 5,
        "use_user_memory": True,
        "enable_personalization": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-chat/chat",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"完整响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"异常: {e}")

def test_news_pipeline_detailed():
    """详细测试新闻处理流水线API"""
    print("\n=== 详细测试新闻处理流水线API ===")
    
    test_data = {
        "query": "人工智能",
        "num_results": 3,  # 减少数量以便快速测试
        "enable_storage": True,
        "enable_vectorization": False,  # 暂时禁用向量化
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,  # 暂时禁用用户记忆
        "max_cards": 2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        # 打印关键信息
        print(f"成功: {result.get('success', False)}")
        print(f"消息: {result.get('message', 'N/A')}")
        print(f"找到新闻: {result.get('total_found', 0)}")
        print(f"处理数量: {result.get('processed_count', 0)}")
        print(f"生成卡片: {result.get('cards_generated', 0)}")
        print(f"向量创建: {result.get('vectors_created', 0)}")
        
        # 检查阶段结果
        stage_results = result.get('stage_results', [])
        print(f"\n阶段结果数量: {len(stage_results)}")
        for i, stage in enumerate(stage_results):
            print(f"阶段 {i+1}: {stage.get('stage', 'unknown')} - 成功: {stage.get('success', False)}")
            if not stage.get('success', False):
                print(f"  错误: {stage.get('error', 'N/A')}")
        
        # 检查错误和警告
        errors = result.get('errors', [])
        warnings = result.get('warnings', [])
        if errors:
            print(f"\n错误: {errors}")
        if warnings:
            print(f"\n警告: {warnings}")
        
        # 检查新闻卡片
        news_cards = result.get('news_cards', [])
        print(f"\n新闻卡片数量: {len(news_cards)}")
        if news_cards:
            print(f"第一张卡片: {json.dumps(news_cards[0], indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    test_enhanced_chat_detailed()
    test_news_pipeline_detailed()
