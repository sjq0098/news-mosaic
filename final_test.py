#!/usr/bin/env python3
"""
最终集成测试 - 验证所有修复的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    """测试完整的工作流程"""
    print("🚀 开始完整工作流程测试...")
    
    # 1. 测试新闻处理流水线
    print("\n📰 步骤1: 测试新闻处理流水线")
    pipeline_data = {
        "query": "科技创新",
        "num_results": 5,
        "enable_storage": True,
        "enable_vectorization": False,  # 暂时禁用以加快测试
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,  # 暂时禁用以加快测试
        "max_cards": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=pipeline_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 新闻处理成功")
            print(f"   - 找到新闻: {result.get('total_found', 0)}")
            print(f"   - 处理数量: {result.get('processed_count', 0)}")
            print(f"   - 生成卡片: {result.get('cards_generated', 0)}")
            
            # 检查新闻卡片
            news_cards = result.get('news_cards', [])
            if news_cards:
                print(f"   - 第一张卡片标题: {news_cards[0].get('title', 'N/A')}")
                print(f"   - 卡片来源: {news_cards[0].get('source', 'N/A')}")
                return True
            else:
                print("   ⚠️ 没有生成新闻卡片")
                return False
        else:
            print(f"❌ 新闻处理失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 新闻处理异常: {e}")
        return False

def test_enhanced_chat():
    """测试增强对话功能"""
    print("\n💬 步骤2: 测试增强对话功能")
    
    chat_data = {
        "user_id": "test_user",
        "message": "请分析一下最新的科技创新趋势",
        "session_id": "test_session_final",
        "max_context_news": 3,
        "use_user_memory": True,
        "enable_personalization": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-chat/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 对话成功")
                print(f"   - 会话ID: {result.get('session_id', 'N/A')}")
                print(f"   - 置信度: {result.get('confidence_score', 0):.2f}")
                print(f"   - 使用tokens: {result.get('tokens_used', 0)}")
                print(f"   - AI回复长度: {len(result.get('ai_response', ''))}")
                return True
            else:
                print(f"❌ 对话失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ 对话请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 对话异常: {e}")
        return False

def test_api_endpoints():
    """测试关键API端点"""
    print("\n🔗 步骤3: 测试关键API端点")
    
    endpoints = [
        "/health",
        "/api/enhanced-chat/health",
        "/api/news-pipeline/health"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - 正常")
                success_count += 1
            else:
                print(f"❌ {endpoint} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - 异常: {e}")
    
    return success_count == len(endpoints)

def main():
    """主测试函数"""
    print("🧪 News Mosaic 最终集成测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务器未运行或不健康")
            return
    except:
        print("❌ 无法连接到后端服务器")
        print("请确保后端服务器正在运行在 http://localhost:8000")
        return
    
    print("✅ 后端服务器连接正常")
    
    # 执行测试
    results = []
    
    # 测试API端点
    results.append(test_api_endpoints())
    
    # 测试新闻处理流水线
    results.append(test_complete_workflow())
    
    # 测试增强对话
    results.append(test_enhanced_chat())
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print(f"总测试项: {len(results)}")
    print(f"成功项: {sum(results)}")
    print(f"失败项: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 所有测试都通过了！")
        print("✨ 项目修复成功，功能正常运行")
        print("\n📝 修复内容总结:")
        print("1. ✅ 修复了智能对话422错误")
        print("2. ✅ 修复了新闻卡片显示空白问题")
        print("3. ✅ 完善了API路由注册")
        print("4. ✅ 修复了数据模型验证问题")
        print("5. ✅ 优化了错误处理机制")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        print("请查看上面的详细错误信息")

if __name__ == "__main__":
    main()
