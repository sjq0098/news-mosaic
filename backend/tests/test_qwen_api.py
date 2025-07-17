#!/usr/bin/env python3
"""
直接测试QWEN API连接
"""

import asyncio
import httpx
import os

async def test_qwen_api():
    """测试QWEN API"""
    # API配置
    api_key = "sk-a33e412fc07b4b6da0fbd9153a18d827"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    print(f"🔗 测试QWEN API连接...")
    print(f"URL: {base_url}")
    print(f"API Key: {api_key[:20]}...")
    
    # 构建请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 50
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("\n📤 发送请求...")
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"📥 状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text[:500]}...")
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"✅ 成功！回复: {content}")
            else:
                print(f"❌ 失败！状态码: {response.status_code}")
                
        except Exception as e:
            print(f"💥 异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_qwen_api()) 