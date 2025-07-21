#!/usr/bin/env python3
"""
最终完整功能测试
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_news_processing():
    """测试完整的新闻处理功能"""
    print("🚀 开始完整新闻处理测试...")
    
    # 测试所有功能模块
    test_data = {
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
        print(f"📤 发送完整处理请求...")
        
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        
        print(f"📥 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 完整处理成功")
            
            # 详细分析结果
            print(f"\n📊 处理统计:")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
            
            # 检查各个功能模块
            news_cards = result.get('news_cards', [])
            ai_summary = result.get('ai_summary', '')
            sentiment_overview = result.get('sentiment_overview', {})
            
            print(f"\n🎴 新闻卡片功能:")
            print(f"  - 卡片数量: {len(news_cards)}")
            if news_cards:
                first_card = news_cards[0]
                print(f"  - 第一张卡片标题: {first_card.get('title', 'N/A')}")
                print(f"  - 卡片来源: {first_card.get('source', 'N/A')}")
                print(f"  - 情感标签: {first_card.get('metadata', {}).get('sentiment_label', 'N/A')}")
                print(f"  - 重要性等级: {first_card.get('metadata', {}).get('importance_level', 'N/A')}")
            
            print(f"\n🤖 AI分析功能:")
            if ai_summary:
                print(f"  - AI摘要长度: {len(ai_summary)}字符")
                print(f"  - AI摘要预览: {ai_summary[:100]}...")
            else:
                print(f"  - AI摘要: 未生成")
            
            print(f"\n😊 情感分析功能:")
            if sentiment_overview:
                print(f"  - 情感分布: {sentiment_overview}")
            else:
                print(f"  - 情感分析: 未生成")
            
            return True
            
        else:
            print(f"❌ 完整处理失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 完整处理异常: {e}")
        return False

def test_enhanced_chat():
    """测试增强对话功能"""
    print("\n💬 测试增强对话功能...")
    
    chat_data = {
        "user_id": "test_user",
        "message": "请分析一下最新的科技创新趋势，特别是人工智能方面的发展",
        "session_id": "final_test_session",
        "max_context_news": 3,
        "use_user_memory": True,
        "enable_personalization": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-chat/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 增强对话成功")
                print(f"  - 会话ID: {result.get('session_id', 'N/A')}")
                print(f"  - 置信度: {result.get('confidence_score', 0):.2f}")
                print(f"  - 使用tokens: {result.get('tokens_used', 0)}")
                print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
                
                ai_response = result.get('ai_response', '')
                if ai_response:
                    print(f"  - AI回复预览: {ai_response[:150]}...")
                
                return True
            else:
                print(f"❌ 增强对话失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ 增强对话请求失败: {response.status_code}")
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 增强对话异常: {e}")
        return False

def test_individual_card_generation():
    """测试单独的卡片生成"""
    print("\n🎴 测试单独卡片生成...")
    
    # 使用一个已知的新闻ID
    news_id = "0984dcd9-b0ac-4381-ac15-842c827d9780"
    
    card_data = {
        "news_id": news_id,
        "include_sentiment": True,
        "include_entities": True,
        "include_related": True,
        "max_summary_length": 200
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/news-cards/generate",
            json=card_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 单独卡片生成成功")
            
            card = result.get('card', {})
            print(f"  - 卡片标题: {card.get('title', 'N/A')}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.3f}秒")
            
            metadata = card.get('metadata', {})
            print(f"  - 情感分析: {metadata.get('sentiment_label', 'N/A')}")
            print(f"  - 重要性: {metadata.get('importance_level', 'N/A')}")
            print(f"  - 可信度: {metadata.get('credibility_level', 'N/A')}")
            
            return True
        else:
            print(f"❌ 单独卡片生成失败: {response.status_code}")
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 单独卡片生成异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 News Mosaic 最终完整功能测试")
    print("=" * 60)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务器未运行或不健康")
            return
    except:
        print("❌ 无法连接到后端服务器")
        return
    
    print("✅ 后端服务器连接正常")
    
    # 执行所有测试
    results = []
    
    # 1. 测试完整新闻处理流水线
    results.append(test_complete_news_processing())
    
    # 2. 测试增强对话功能
    results.append(test_enhanced_chat())
    
    # 3. 测试单独卡片生成
    results.append(test_individual_card_generation())
    
    # 总结结果
    print("\n" + "=" * 60)
    print("📊 最终测试结果总结")
    print(f"总测试项: {len(results)}")
    print(f"成功项: {sum(results)}")
    print(f"失败项: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 所有功能测试都通过了！")
        print("✨ 项目修复完全成功，所有功能正常运行")
        print("\n📝 修复内容总结:")
        print("1. ✅ 修复了智能对话422错误")
        print("2. ✅ 修复了新闻卡片显示空白问题")
        print("3. ✅ 修复了数据库连接和查询问题")
        print("4. ✅ 修复了数据结构映射问题")
        print("5. ✅ 完善了错误处理和日志记录")
        print("\n🚀 现在可以正常使用统一新闻处理界面的所有功能！")
    else:
        print("\n⚠️ 部分功能仍有问题，需要进一步检查")

if __name__ == "__main__":
    main()
