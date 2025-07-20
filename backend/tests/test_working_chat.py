#!/usr/bin/env python3
"""
工作的对话测试 - 直接使用正确的API配置
"""

import asyncio
import httpx
import json

class WorkingQWENService:
    """工作的QWEN服务"""
    
    def __init__(self):
        self.api_key = "sk-a33e412fc07b4b6da0fbd9153a18d827"
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = "qwen-plus"
    
    async def chat(self, message: str) -> str:
        """对话"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"API错误: {response.status_code}"
                    
            except Exception as e:
                return f"请求异常: {e}"

async def test_chat():
    """测试对话"""
    service = WorkingQWENService()
    
    print("🎯 工作的QWEN对话测试")
    print("=" * 50)
    
    # 测试几个问题
    questions = [
        "你好，你是谁？",
        "这个技术突破对中国AI产业有什么具体影响？",
        "请分析一下当前的新闻热点"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n🔸 问题 {i}: {question}")
        print("-" * 30)
        
        response = await service.chat(question)
        print(f"🤖 回复: {response}")
        print()

if __name__ == "__main__":
    asyncio.run(test_chat()) 