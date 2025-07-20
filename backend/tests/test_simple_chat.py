#!/usr/bin/env python3
"""
简化的QWEN对话测试 - 绕过复杂的数据验证
"""

import asyncio
from services.qwen_service import QWENService
from mock_data.news_samples import mock_news_db


async def test_simple_qwen_chat():
    """测试简单的QWEN对话功能"""
    print("🤖 测试简化的QWEN对话功能...")
    
    # 初始化服务
    qwen_service = QWENService()
    
    # 获取一条测试新闻
    all_news = mock_news_db.get_all_news()
    test_news = all_news[0]  # AI大模型新闻
    
    print(f"📰 测试新闻: {test_news['title']}")
    
    # 构建简单的对话提示
    user_query = "最近AI领域有什么重大突破？请详细分析一下"
    
    # 构建上下文
    news_context = f"""
相关新闻：
标题：{test_news['title']}
内容：{test_news['content'][:500]}...
来源：{test_news['source']}
"""
    
    # 构建完整提示
    full_prompt = f"""
你是一个专业的新闻分析助手。请根据提供的新闻信息回答用户问题。

{news_context}

用户问题：{user_query}

请提供专业、详细的分析回复：
"""
    
    print(f"\n👤 用户查询: {user_query}")
    print("\n🔄 调用QWEN API...")
    
    try:
        # 直接调用QWEN API
        response = await qwen_service.generate_response(
            user_message=full_prompt,
            chat_history=[],
            include_news=False,  # 不包含新闻搜索
            temperature=0.7,
            max_tokens=800
        )
        
        print(f"\n✅ QWEN API调用成功！")
        print(f"🤖 AI回复: {response.content}")
        print(f"📊 使用token数: {response.tokens_used}")
        print(f"⏱️ 生成时间: {response.generation_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"\n❌ QWEN API调用失败: {e}")
        return False


async def test_multiple_queries():
    """测试多个查询"""
    print("\n" + "="*60)
    print("🔄 测试多个查询...")
    
    qwen_service = QWENService()
    all_news = mock_news_db.get_all_news()
    
    test_cases = [
        {
            "news": all_news[0],  # AI新闻
            "query": "这个AI技术突破有什么重要意义？"
        },
        {
            "news": all_news[2],  # 新能源汽车
            "query": "新能源汽车市场的发展趋势如何？"
        },
        {
            "news": all_news[3],  # 量子计算
            "query": "量子计算的实用化还需要多长时间？"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📍 测试 {i}/3: {case['news']['title'][:40]}...")
        
        news_context = f"新闻：{case['news']['title']}\n内容：{case['news']['content'][:300]}..."
        full_prompt = f"{news_context}\n\n问题：{case['query']}\n\n请简要回答："
        
        try:
            response = await qwen_service.generate_response(
                user_message=full_prompt,
                include_news=False,
                max_tokens=300,
                temperature=0.6
            )
            
            print(f"✅ 回复成功: {response.content[:150]}...")
            print(f"   耗时: {response.generation_time:.2f}秒")
            
        except Exception as e:
            print(f"❌ 回复失败: {e}")


async def main():
    """主测试流程"""
    print("🚀 启动简化QWEN对话测试")
    print("="*60)
    
    # 测试1: 基础对话功能
    success = await test_simple_qwen_chat()
    
    if success:
        # 测试2: 多个查询
        await test_multiple_queries()
        
        print("\n" + "="*60)
        print("🎉 简化对话测试完成！")
        print("✅ QWEN API正常工作")
        print("✅ 能够基于新闻上下文生成智能回复")
        print("\n💡 问题诊断：")
        print("   • QWEN API本身工作正常")
        print("   • 问题出在NewsCardMetadata数据验证")
        print("   • 需要修复数据模型的中英文字段映射")
    else:
        print("\n❌ QWEN API存在问题，需要进一步诊断")


if __name__ == "__main__":
    asyncio.run(main()) 