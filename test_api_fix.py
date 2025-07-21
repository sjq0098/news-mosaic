#!/usr/bin/env python3
"""
测试修复后的API功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.status_code == 200

def test_enhanced_chat():
    """测试增强对话API"""
    print("\n=== 测试增强对话API ===")
    
    # 测试数据
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
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 增强对话API测试成功")
            print(f"成功: {result.get('success', False)}")
            print(f"会话ID: {result.get('session_id', 'N/A')}")
            return True
        else:
            print(f"❌ 增强对话API测试失败")
            print(f"错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 增强对话API测试异常: {e}")
        return False

def test_news_pipeline():
    """测试新闻处理流水线API"""
    print("\n=== 测试新闻处理流水线API ===")
    
    test_data = {
        "query": "人工智能",
        "num_results": 5,
        "enable_storage": True,
        "enable_vectorization": True,
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": True,
        "max_cards": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 新闻处理流水线API测试成功")
            print(f"成功: {result.get('success', False)}")
            print(f"找到新闻: {result.get('total_found', 0)}")
            print(f"生成卡片: {result.get('cards_generated', 0)}")
            print(f"新闻卡片数量: {len(result.get('news_cards', []))}")
            
            # 检查新闻卡片内容
            cards = result.get('news_cards', [])
            if cards:
                print(f"第一张卡片标题: {cards[0].get('title', 'N/A')}")
            
            return True
        else:
            print(f"❌ 新闻处理流水线API测试失败")
            print(f"错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 新闻处理流水线API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试修复后的API功能...")
    
    results = []
    
    # 测试健康检查
    results.append(test_health())
    
    # 等待一下
    time.sleep(1)
    
    # 测试增强对话API
    results.append(test_enhanced_chat())
    
    # 等待一下
    time.sleep(2)
    
    # 测试新闻处理流水线API
    results.append(test_news_pipeline())
    
    # 总结结果
    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {len(results)}")
    print(f"成功数: {sum(results)}")
    print(f"失败数: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
