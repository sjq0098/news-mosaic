"""
测试API接口
"""

import requests
import json

def test_news_pipeline_api():
    """测试新闻处理流水线API"""
    url = "http://localhost:8000/api/news-pipeline/process"
    
    # 测试数据
    data = {
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
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token"  # 测试token
    }
    
    try:
        print(f"发送请求到: {url}")
        print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")


def test_health_check():
    """测试健康检查"""
    url = "http://localhost:8000/api/news-pipeline/health"

    try:
        response = requests.get(url)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.text}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")


def test_enhanced_chat():
    """测试增强对话API"""
    url = "http://localhost:8000/api/enhanced-chat/chat"

    data = {
        "user_id": "demo_user",
        "message": "最近有什么人工智能的新闻吗？",
        "session_id": None,
        "max_context_news": 3,
        "similarity_threshold": 0.7,
        "temperature": 0.7,
        "max_tokens": 800,
        "use_user_memory": True,
        "include_related_news": True,
        "enable_personalization": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token"
    }

    try:
        print(f"发送对话请求到: {url}")
        print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        response = requests.post(url, json=data, headers=headers)

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 对话API调用成功!")
            ai_response = result.get('ai_response', 'N/A')
            print(f"AI回复: {ai_response[:200]}..." if len(ai_response) > 200 else f"AI回复: {ai_response}")
            print(f"置信度: {result.get('confidence_score', 'N/A')}")
            print(f"相关新闻数量: {result.get('sources_count', 'N/A')}")
            print(f"会话ID: {result.get('session_id', 'N/A')}")
        else:
            print(f"❌ 对话API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"❌ 对话请求异常: {e}")


if __name__ == "__main__":
    print("🧪 开始API测试...")
    print("=" * 50)

    # 先测试健康检查
    test_health_check()

    print("\n" + "=" * 50)

    # 测试新闻处理API
    test_news_pipeline_api()

    print("\n" + "=" * 50)

    # 测试增强对话API
    test_enhanced_chat()
