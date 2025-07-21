#!/usr/bin/env python3
"""
测试前端发送的请求
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_frontend_like_request():
    """测试和前端一样的请求"""
    print("🔍 测试前端类似的请求...")
    
    # 模拟前端发送的请求数据
    test_data = {
        "query": "南开",
        "num_results": 10,
        "enable_storage": True,
        "enable_vectorization": True,  # 前端启用了这个
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": True,  # 前端启用了这个
        "max_cards": 5,
        "personalization_level": 0.5
    }
    
    try:
        print(f"📤 发送请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MzcxNzY0MDB9.qxi7JlfppThzws_AtRF3IASv1OPil1BebJdLiY8VGHg"
            },
            timeout=60  # 增加超时时间
        )
        
        elapsed_time = time.time() - start_time
        print(f"📥 状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
            
            # 检查是否有错误
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            if errors:
                print(f"❌ 错误: {errors}")
            if warnings:
                print(f"⚠️ 警告: {warnings}")
                
        else:
            print(f"❌ 请求失败")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"⏰ 请求超时（超过60秒）")
    except Exception as e:
        print(f"💥 异常: {e}")

def test_simplified_request():
    """测试简化的请求（禁用耗时功能）"""
    print("\n🔍 测试简化的请求...")
    
    # 禁用耗时的功能
    test_data = {
        "query": "南开",
        "num_results": 5,  # 减少数量
        "enable_storage": True,
        "enable_vectorization": False,  # 禁用向量化
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,  # 禁用用户记忆
        "max_cards": 3
    }
    
    try:
        print(f"📤 发送简化请求...")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=test_data,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        print(f"📥 状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 简化请求成功")
            print(f"  - 成功: {result.get('success', False)}")
            print(f"  - 找到新闻: {result.get('total_found', 0)}")
            print(f"  - 处理数量: {result.get('processed_count', 0)}")
            print(f"  - 生成卡片: {result.get('cards_generated', 0)}")
            print(f"  - 处理时间: {result.get('processing_time', 0):.2f}秒")
            
            return True
        else:
            print(f"❌ 简化请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 简化请求异常: {e}")
        return False

if __name__ == "__main__":
    # 先测试简化请求
    if test_simplified_request():
        print("\n" + "="*50)
        # 如果简化请求成功，再测试完整请求
        test_frontend_like_request()
    else:
        print("\n❌ 简化请求都失败了，需要检查后端服务")
