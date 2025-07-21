#!/usr/bin/env python3
"""
模拟前端请求测试
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def simulate_frontend_request():
    """模拟前端发送的请求"""
    print("🌐 模拟前端请求测试...")
    
    # 模拟前端修复后的默认配置
    test_data = {
        "query": "南开",
        "num_results": 10,
        "enable_storage": True,
        "enable_vectorization": False,  # 前端默认关闭
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,  # 前端默认关闭
        "max_cards": 5,
        "personalization_level": 0.5
    }
    
    try:
        print(f"📤 发送模拟前端请求...")
        print(f"🔧 配置: 向量化={test_data['enable_vectorization']}, 用户记忆={test_data['enable_user_memory']}")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token"  # 模拟前端token
            },
            timeout=120  # 2分钟超时，和前端一致
        )
        
        elapsed_time = time.time() - start_time
        print(f"📥 状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ 前端请求模拟成功！")
                print(f"\n📊 处理结果:")
                print(f"  - 找到新闻: {result.get('total_found', 0)}")
                print(f"  - 处理数量: {result.get('processed_count', 0)}")
                print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
                print(f"  - 后端处理时间: {result.get('processing_time', 0):.2f}秒")
                
                # 检查新闻卡片
                news_cards = result.get('news_cards', [])
                if news_cards:
                    print(f"\n🎴 新闻卡片:")
                    for i, card in enumerate(news_cards[:3], 1):  # 显示前3张
                        print(f"  {i}. {card.get('title', 'N/A')}")
                        print(f"     来源: {card.get('source', 'N/A')}")
                        metadata = card.get('metadata', {})
                        print(f"     情感: {metadata.get('sentiment_label', 'N/A')}")
                        print(f"     重要性: {metadata.get('importance_level', 'N/A')}")
                
                # 检查AI分析
                ai_summary = result.get('ai_summary', '')
                if ai_summary:
                    print(f"\n🤖 AI分析摘要:")
                    print(f"  {ai_summary[:200]}...")
                
                # 检查情感分析
                sentiment = result.get('sentiment_overview', {})
                if sentiment:
                    total = sentiment.get('total_analyzed', 0)
                    positive = sentiment.get('positive', {}).get('percentage', 0)
                    negative = sentiment.get('negative', {}).get('percentage', 0)
                    neutral = sentiment.get('neutral', {}).get('percentage', 0)
                    print(f"\n😊 情感分析:")
                    print(f"  分析了{total}条新闻")
                    print(f"  积极: {positive}%, 消极: {negative}%, 中性: {neutral}%")
                
                print(f"\n🎯 前端界面应该显示:")
                print(f"  ✅ 处理概览 - 显示统计数据")
                print(f"  ✅ 处理流程 - 显示各阶段状态")
                print(f"  ✅ 情感分析 - 显示情感分布")
                print(f"  ✅ 新闻卡片 - 显示{len(news_cards)}张卡片")
                print(f"  ✅ 智能对话 - 可以进行AI对话")
                
                return True
            else:
                print(f"❌ 处理失败: {result.get('message', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ 请求超时（超过2分钟）")
        print(f"❌ 这意味着前端仍会显示超时错误")
        return False
    except Exception as e:
        print(f"💥 异常: {e}")
        return False

def test_chat_functionality():
    """测试智能对话功能"""
    print("\n💬 测试智能对话功能...")
    
    chat_data = {
        "user_id": "test_user",
        "message": "请分析一下南开相关的新闻",
        "session_id": "frontend_test_session",
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
                print(f"✅ 智能对话功能正常")
                print(f"  - 会话ID: {result.get('session_id', 'N/A')}")
                print(f"  - 置信度: {result.get('confidence_score', 0):.2f}")
                print(f"  - AI回复长度: {len(result.get('ai_response', ''))}")
                return True
            else:
                print(f"❌ 智能对话失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ 智能对话请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 智能对话异常: {e}")
        return False

if __name__ == "__main__":
    print("🧪 前端功能模拟测试")
    print("=" * 60)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务器未运行")
            exit(1)
    except:
        print("❌ 无法连接到后端服务器")
        exit(1)
    
    print("✅ 后端服务器连接正常")
    
    # 执行测试
    success1 = simulate_frontend_request()
    success2 = test_chat_functionality()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    
    if success1 and success2:
        print("🎉 所有功能测试通过！")
        print("✨ 前端现在应该可以正常工作了")
        print("\n📝 用户使用指南:")
        print("1. 在统一新闻处理界面输入关键词（如'南开'）")
        print("2. 点击搜索，等待10-15秒")
        print("3. 查看5个标签页的内容:")
        print("   - 处理概览：显示处理统计")
        print("   - 处理流程：显示各阶段状态")
        print("   - 情感分析：显示情感分布图表")
        print("   - 新闻卡片：显示生成的新闻卡片")
        print("   - 智能对话：进行AI对话交互")
        print("\n🚀 问题已完全解决！")
    else:
        print("⚠️ 部分功能仍有问题")
        if not success1:
            print("❌ 新闻处理功能异常")
        if not success2:
            print("❌ 智能对话功能异常")
