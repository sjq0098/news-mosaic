#!/usr/bin/env python3
"""
简单测试Markdown功能
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.qwen_service import QWENService

async def test_qwen_markdown():
    """测试QWEN服务的Markdown回答"""
    
    print("🧪 测试QWEN服务的Markdown功能...")
    
    # 创建QWEN服务（演示模式）
    qwen_service = QWENService()
    
    test_questions = [
        "请分析一下最新的科技趋势",
        "预测未来人工智能的发展",
        "比较不同的技术方案",
        "总结今天的重要新闻"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 问题 {i}: {question}")
        print("-" * 50)
        
        try:
            response = await qwen_service.generate_response(
                user_message=question,
                chat_history=[],
                include_news=False,
                temperature=0.7,
                max_tokens=500
            )
            
            print("✅ 生成成功！")
            print(f"📊 Token使用: {response.tokens_used}")
            print(f"⏱️  生成时间: {response.generation_time:.2f}秒")
            print("\n📝 回答内容:")
            print("=" * 60)
            print(response.content)
            print("=" * 60)
            
            # 检查Markdown格式
            markdown_indicators = ["##", "###", "**", "*", "-", "1.", ">", "`"]
            found_indicators = [ind for ind in markdown_indicators if ind in response.content]
            
            if found_indicators:
                print(f"✅ 检测到Markdown格式: {', '.join(found_indicators)}")
            else:
                print("⚠️  未检测到明显的Markdown格式")
                
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")

async def main():
    """主函数"""
    print("🚀 简单Markdown测试开始")
    print("="*60)
    
    await test_qwen_markdown()
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("\n💡 说明：")
    print("   - 这是演示模式的测试")
    print("   - 如果看到 ## ### ** 等标记，说明Markdown格式正常")
    print("   - 前端会将这些标记渲染为格式化的文本")

if __name__ == "__main__":
    asyncio.run(main())
