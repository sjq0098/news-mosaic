#!/usr/bin/env python3
"""
测试Markdown集成功能
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_rag_chat_service import EnhancedRAGChatService, RAGChatRequest

async def test_markdown_response():
    """测试Markdown格式的AI回答"""
    
    print("🧪 开始测试Markdown集成功能...")
    
    # 创建RAG聊天服务
    rag_service = EnhancedRAGChatService()
    
    # 测试请求
    test_request = RAGChatRequest(
        user_id="test_user",
        message="请分析一下最近的科技新闻趋势",
        session_id="test_session_001",
        max_context_news=3,
        use_user_memory=False,
        enable_personalization=False
    )
    
    try:
        print("📤 发送测试请求...")
        response = await rag_service.chat_with_rag(test_request)
        
        if response.success:
            print("✅ 请求成功！")
            print("\n" + "="*50)
            print("📝 AI回答内容（Markdown格式）：")
            print("="*50)
            print(response.ai_response)
            print("="*50)
            
            # 检查是否包含Markdown格式
            markdown_indicators = [
                "##", "###", "**", "*", "-", "1.", ">", "`"
            ]
            
            has_markdown = any(indicator in response.ai_response for indicator in markdown_indicators)
            
            if has_markdown:
                print("✅ 检测到Markdown格式标记")
            else:
                print("⚠️  未检测到明显的Markdown格式标记")
                
            print(f"\n📊 响应统计：")
            print(f"   - 置信度: {response.confidence_score:.2f}")
            print(f"   - 处理时间: {response.processing_time:.2f}秒")
            print(f"   - 相关新闻数量: {len(response.relevant_news)}")
            print(f"   - 会话ID: {response.session_id}")
            
        else:
            print(f"❌ 请求失败: {response.message}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_multiple_questions():
    """测试多个问题的Markdown回答"""
    
    print("\n🔄 测试多个问题...")
    
    rag_service = EnhancedRAGChatService()
    
    test_questions = [
        "什么是人工智能的最新发展？",
        "请比较不同的新闻来源",
        "预测一下未来的技术趋势",
        "总结今天的重要新闻"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 问题 {i}: {question}")
        
        request = RAGChatRequest(
            user_id="test_user",
            message=question,
            session_id=f"test_session_{i:03d}",
            max_context_news=2
        )
        
        try:
            response = await rag_service.chat_with_rag(request)
            
            if response.success:
                print(f"✅ 回答长度: {len(response.ai_response)} 字符")
                
                # 检查Markdown元素
                markdown_count = sum([
                    response.ai_response.count("##"),
                    response.ai_response.count("**"),
                    response.ai_response.count("- "),
                    response.ai_response.count("> ")
                ])
                
                print(f"📊 Markdown元素数量: {markdown_count}")
                
                # 显示前100个字符
                preview = response.ai_response[:100].replace('\n', ' ')
                print(f"👀 预览: {preview}...")
                
            else:
                print(f"❌ 失败: {response.message}")
                
        except Exception as e:
            print(f"❌ 错误: {str(e)}")

async def main():
    """主测试函数"""
    print("🚀 Markdown集成测试开始")
    print("="*60)
    
    await test_markdown_response()
    await test_multiple_questions()
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("\n💡 提示：")
    print("   - 如果看到Markdown格式标记，说明后端正常工作")
    print("   - 前端应该能够正确渲染这些Markdown内容")
    print("   - 可以在浏览器中访问 http://localhost:3001/test-markdown 查看渲染效果")

if __name__ == "__main__":
    asyncio.run(main())
