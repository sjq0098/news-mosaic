#!/usr/bin/env python3
"""
测试优化后的请求
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_optimized_full_request():
    """测试优化后的完整请求"""
    print("🔍 测试优化后的完整请求...")
    
    # 和前端一样的请求，但使用优化后的后端
    test_data = {
        "query": "南开",
        "num_results": 10,
        "enable_storage": True,
        "enable_vectorization": True,  # 现在限制了数量
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": True,  # 现在简化了逻辑
        "max_cards": 5,
        "personalization_level": 0.5
    }
    
    try:
        print(f"📤 发送优化后的完整请求...")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            timeout=90  # 90秒超时
        )
        
        elapsed_time = time.time() - start_time
        print(f"📥 状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 优化后的完整请求成功")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            print(f"  - 向量创建: {result.get('vectors_created', 0)}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
            
            # 检查各个功能模块
            stage_results = result.get('stage_results', [])
            print(f"\n📋 阶段执行结果:")
            for stage in stage_results:
                stage_name = stage.get('stage', 'unknown')
                success = stage.get('success', False)
                processing_time = stage.get('processing_time', 0)
                print(f"  - {stage_name}: {'✅' if success else '❌'} ({processing_time:.2f}s)")
            
            # 检查AI分析和情感分析
            ai_summary = result.get('ai_summary', '')
            sentiment_overview = result.get('sentiment_overview', {})
            
            if ai_summary:
                print(f"\n🤖 AI分析: 生成了 {len(ai_summary)} 字符的摘要")
            
            if sentiment_overview:
                total = sentiment_overview.get('total_analyzed', 0)
                positive = sentiment_overview.get('positive', {}).get('percentage', 0)
                negative = sentiment_overview.get('negative', {}).get('percentage', 0)
                neutral = sentiment_overview.get('neutral', {}).get('percentage', 0)
                print(f"😊 情感分析: {total}条新闻 - 积极{positive}% 消极{negative}% 中性{neutral}%")
            
            return True
            
        else:
            print(f"❌ 优化后的完整请求失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ 请求超时（超过90秒）")
        return False
    except Exception as e:
        print(f"💥 异常: {e}")
        return False

def test_frontend_default_config():
    """测试前端默认配置（优化后）"""
    print("\n🔍 测试前端默认配置（优化后）...")
    
    # 前端优化后的默认配置
    test_data = {
        "query": "南开",
        "num_results": 10,
        "enable_storage": True,
        "enable_vectorization": False,  # 默认关闭
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,  # 默认关闭
        "max_cards": 5,
        "personalization_level": 0.5
    }
    
    try:
        print(f"📤 发送前端默认配置请求...")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            timeout=60  # 60秒超时
        )
        
        elapsed_time = time.time() - start_time
        print(f"📥 状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 前端默认配置请求成功")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
            
            return True
            
        else:
            print(f"❌ 前端默认配置请求失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 异常: {e}")
        return False

if __name__ == "__main__":
    print("🧪 测试优化后的新闻处理功能")
    print("=" * 50)
    
    # 测试前端默认配置
    success1 = test_frontend_default_config()
    
    if success1:
        print("\n" + "="*50)
        # 测试完整功能
        success2 = test_optimized_full_request()
        
        if success1 and success2:
            print("\n🎉 所有测试都成功！")
            print("✨ 前端现在应该可以正常工作了")
        else:
            print("\n⚠️ 部分测试失败")
    else:
        print("\n❌ 基础功能测试失败")
