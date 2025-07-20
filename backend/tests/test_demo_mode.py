#!/usr/bin/env python3
"""
测试演示模式是否正确工作
"""

import asyncio
from core.config import settings
from services.qwen_service import QWENService
from services.news_chat_service import NewsChatService

async def test_demo_mode():
    """测试演示模式"""
    print("🔍 测试演示模式配置...")
    
    # 检查配置
    print(f"QWEN_API_KEY: {settings.QWEN_API_KEY}")
    print(f"API配置状态: {settings.is_api_configured('qwen')}")
    
    # 测试QWEN服务
    qwen_service = QWENService()
    print(f"QWEN演示模式: {qwen_service.demo_mode}")
    
    # 测试对话服务
    chat_service = NewsChatService()
    print(f"Chat QWEN演示模式: {chat_service.qwen_service.demo_mode}")
    
    # 测试生成回复
    print("\n🤖 测试生成回复...")
    try:
        response = await qwen_service.generate_response("这是一个测试问题")
        print(f"✅ 回复成功: {response.content[:100]}...")
    except Exception as e:
        print(f"❌ 回复失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_demo_mode()) 