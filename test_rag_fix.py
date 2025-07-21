#!/usr/bin/env python3
"""
测试RAG对话修复是否有效
"""

import asyncio
import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "test_user",
    "password": "test123456",
    "email": "test@example.com"
}

async def test_rag_conversation():
    """测试RAG对话功能"""
    print("🔍 测试RAG对话修复...")
    
    # 1. 首先进行新闻搜索和处理（启用向量化）
    print("\n📰 步骤1: 搜索并处理新闻（启用向量化）...")
    
    news_request = {
        "query": "人工智能",
        "num_results": 5,
        "enable_storage": True,
        "enable_vectorization": True,  # 关键：启用向量化
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=news_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 新闻处理成功:")
            print(f"   - 找到新闻: {result.get('total_found', 0)} 条")
            print(f"   - 处理数量: {result.get('processed_count', 0)} 条")
            print(f"   - 创建向量: {result.get('vectors_created', 0)} 个")
            print(f"   - 生成卡片: {result.get('cards_generated', 0)} 张")
            
            if result.get('vectors_created', 0) == 0:
                print("⚠️ 警告: 没有创建向量，RAG对话可能无法正常工作")
                return False
                
        else:
            print(f"❌ 新闻处理失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 新闻处理异常: {e}")
        return False
    
    # 等待一下让向量化完成
    print("\n⏳ 等待向量化完成...")
    time.sleep(3)
    
    # 2. 测试RAG对话
    print("\n🤖 步骤2: 测试RAG对话...")
    
    chat_request = {
        "user_id": "test_user",
        "message": "刚刚搜索到的人工智能新闻有什么重要内容？",
        "max_context_news": 5,
        "similarity_threshold": 0.5,  # 降低阈值以增加匹配概率
        "use_user_memory": True,
        "enable_personalization": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-chat/chat",
            json=chat_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RAG对话成功:")
            print(f"   - 成功状态: {result.get('success', False)}")
            print(f"   - 置信度: {result.get('confidence_score', 0):.1%}")
            print(f"   - 来源数量: {result.get('sources_count', 0)} 条新闻")
            print(f"   - AI回复: {result.get('ai_response', '')[:100]}...")
            
            # 检查是否成功检索到相关新闻
            if result.get('sources_count', 0) > 0:
                print("🎉 RAG对话修复成功！能够检索到相关新闻")
                return True
            else:
                print("❌ RAG对话仍有问题：没有检索到相关新闻")
                return False
                
        else:
            print(f"❌ RAG对话失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAG对话异常: {e}")
        return False

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试RAG对话修复...")
    print("=" * 60)
    
    # 检查后端服务
    if not test_api_health():
        print("\n❌ 后端服务不可用，请先启动后端服务")
        return
    
    # 执行RAG对话测试
    success = await test_rag_conversation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 RAG对话修复测试通过！")
        print("✨ 现在智能对话应该能够正确检索和分析新闻内容了")
    else:
        print("❌ RAG对话修复测试失败")
        print("💡 建议检查:")
        print("   1. 向量化是否正确启用")
        print("   2. 向量数据库是否正常工作")
        print("   3. 新闻是否正确存储到数据库")

if __name__ == "__main__":
    asyncio.run(main())
