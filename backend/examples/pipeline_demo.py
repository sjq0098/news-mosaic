#!/usr/bin/env python3
"""
B端完整流水线演示 - 向量检索 & LLM调度
从模拟新闻数据库到智能回复的端到端测试
"""

import asyncio
import json
import time
from datetime import datetime

from services.rag_pipeline_service import rag_pipeline
from mock_data.news_samples import mock_news_db


async def print_banner(title: str):
    """打印标题横幅"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)


async def print_step(step_num: int, description: str):
    """打印步骤信息"""
    print(f"\n📍 步骤 {step_num}: {description}")
    print("-" * 60)


async def demo_pipeline_initialization():
    """演示流水线初始化过程"""
    await print_banner("RAG流水线初始化演示")
    
    print("📊 模拟新闻数据概览:")
    all_news = mock_news_db.get_all_news()
    
    categories = {}
    for news in all_news:
        category = news["category"]
        categories[category] = categories.get(category, 0) + 1
    
    print(f"📰 总新闻数量: {len(all_news)}")
    print("📂 新闻分类分布:")
    for category, count in categories.items():
        print(f"   • {category}: {count} 条")
    
    print("\n🔄 开始初始化流水线...")
    start_time = time.time()
    
    await rag_pipeline.initialize_pipeline()
    
    init_time = time.time() - start_time
    print(f"✅ 流水线初始化完成，耗时: {init_time:.2f}秒")
    
    # 显示状态
    status = await rag_pipeline.get_pipeline_status()
    print(f"\n📈 流水线状态:")
    print(f"   • 已处理新闻: {status['total_news']} 条")
    print(f"   • 向量存储大小: {status['vector_store_size']}")
    print(f"   • 新闻分类: {', '.join(status['categories'])}")


async def demo_news_search():
    """演示新闻检索功能"""
    await print_banner("新闻检索功能演示")
    
    test_queries = [
        "AI大模型技术突破",
        "新能源汽车发展",
        "量子计算研究进展",
        "5G网络建设"
    ]
    
    for i, query in enumerate(test_queries, 1):
        await print_step(i, f"检索查询: '{query}'")
        
        start_time = time.time()
        relevant_news = await rag_pipeline.search_relevant_news(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"🔍 检索耗时: {search_time:.3f}秒")
        print(f"📊 找到相关新闻: {len(relevant_news)} 条")
        
        for j, news_item in enumerate(relevant_news, 1):
            news = news_item["news_data"]
            similarity = news_item["similarity_score"]
            print(f"   {j}. [{similarity:.3f}] {news['title'][:60]}...")
            print(f"      来源: {news['source']} | 分类: {news['category']}")
        
        if i < len(test_queries):
            print()


async def demo_complete_pipeline():
    """演示完整流水线端到端过程"""
    await print_banner("完整RAG流水线端到端演示")
    
    test_scenarios = [
        {
            "query": "最近AI领域有什么重大突破？请详细分析一下",
            "description": "AI技术突破分析"
        },
        {
            "query": "新能源汽车的市场表现如何？有什么发展趋势？",
            "description": "新能源汽车市场分析"
        },
        {
            "query": "量子计算技术的实用化前景怎么样？",
            "description": "量子计算发展前景"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        await print_step(i, scenario["description"])
        
        print(f"👤 用户查询: {scenario['query']}")
        print("\n🤖 开始处理...")
        
        # 运行完整流水线
        result = await rag_pipeline.demo_complete_pipeline(scenario["query"])
        
        if "error" in result:
            print(f"❌ 处理失败: {result['error']}")
            continue
        
        # 显示处理步骤
        print("\n📋 处理步骤:")
        for step in result["steps"]:
            print(f"   • {step['step']}: {step['description']} ({step['time']:.3f}秒)")
            if "data" in step and isinstance(step["data"], list):
                for item in step["data"][:2]:  # 只显示前2个
                    print(f"     - {item}")
        
        # 显示最终结果
        final_result = result["final_result"]
        if final_result and "ai_response" in final_result:
            print(f"\n🤖 AI回复:")
            response = final_result["ai_response"]
            # 截取回复的前500字符
            if len(response) > 500:
                print(f"   {response[:500]}...")
            else:
                print(f"   {response}")
            
            print(f"\n📊 处理统计:")
            print(f"   • 相关新闻数: {final_result.get('relevant_news_count', 0)}")
            if final_result.get('session_id'):
                print(f"   • 会话ID: {final_result['session_id'][:20]}...")
            print(f"   • 建议问题数: {len(final_result.get('suggested_questions', []))}")
            print(f"   • 总处理时间: {result['total_time']:.2f}秒")
        else:
            print(f"\n❌ 未能生成有效回复")
            print(f"   • 总处理时间: {result['total_time']:.2f}秒")
        
        if i < len(test_scenarios):
            print("\n" + "─" * 60)


async def demo_interactive_chat():
    """演示交互式对话功能"""
    await print_banner("交互式新闻对话演示")
    
    # 模拟多轮对话
    chat_session = None
    conversation = [
        "请介绍一下最近的AI技术发展",
        "这些技术突破对中国有什么影响？",
        "相比其他国家，中国的优势在哪里？",
        "未来几年的发展趋势如何？"
    ]
    
    for i, user_input in enumerate(conversation, 1):
        await print_step(i, f"对话轮次 {i}")
        
        print(f"👤 用户: {user_input}")
        
        start_time = time.time()
        chat_result = await rag_pipeline.chat_with_news_context(
            user_input, 
            session_id=chat_session
        )
        chat_time = time.time() - start_time
        
        if "error" in chat_result:
            print(f"❌ 对话失败: {chat_result['error']}")
            break
        
        # 更新会话ID
        if not chat_session:
            chat_session = chat_result["session_id"]
            print(f"🆕 创建新会话: {chat_session[:20]}...")
        
        print(f"🤖 AI回复: {chat_result['ai_response'][:300]}...")
        print(f"⏱️  回复耗时: {chat_time:.2f}秒")
        
        # 显示相关新闻
        if chat_result["relevant_news"]:
            print(f"📰 参考新闻:")
            for news in chat_result["relevant_news"][:2]:
                print(f"   • {news['title'][:50]}... (相似度: {news['similarity']:.3f})")
        
        if i < len(conversation):
            print()


async def demo_performance_test():
    """演示性能测试"""
    await print_banner("性能测试演示")
    
    print("🔄 运行批量查询性能测试...")
    
    test_queries = [
        "AI技术发展",
        "新能源汽车",
        "5G网络",
        "量子计算",
        "半导体产业"
    ]
    
    # 并发测试
    concurrent_start = time.time()
    concurrent_tasks = [
        rag_pipeline.search_relevant_news(query, top_k=3) 
        for query in test_queries
    ]
    concurrent_results = await asyncio.gather(*concurrent_tasks)
    concurrent_time = time.time() - concurrent_start
    
    # 顺序测试
    sequential_start = time.time()
    sequential_results = []
    for query in test_queries:
        result = await rag_pipeline.search_relevant_news(query, top_k=3)
        sequential_results.append(result)
    sequential_time = time.time() - sequential_start
    
    print(f"📊 性能测试结果:")
    print(f"   • 查询数量: {len(test_queries)}")
    print(f"   • 并发执行时间: {concurrent_time:.3f}秒")
    print(f"   • 顺序执行时间: {sequential_time:.3f}秒")
    print(f"   • 性能提升: {sequential_time/concurrent_time:.2f}x")
    
    # 检查结果一致性
    results_match = all(
        len(concurrent_results[i]) == len(sequential_results[i])
        for i in range(len(test_queries))
    )
    print(f"   • 结果一致性: {'✅ 通过' if results_match else '❌ 失败'}")


async def main():
    """主演示流程"""
    print("🚀 启动B端RAG流水线完整演示")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start = time.time()
    
    try:
        # 1. 流水线初始化
        await demo_pipeline_initialization()
        
        # 2. 新闻检索演示
        await demo_news_search()
        
        # 3. 完整流水线演示
        await demo_complete_pipeline()
        
        # 4. 交互式对话演示
        await demo_interactive_chat()
        
        # 5. 性能测试
        await demo_performance_test()
        
        total_time = time.time() - total_start
        
        await print_banner("演示完成")
        print(f"🎉 所有演示已完成！")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        print(f"📊 演示统计:")
        
        status = await rag_pipeline.get_pipeline_status()
        print(f"   • 处理新闻总数: {status['total_news']}")
        print(f"   • 向量存储大小: {status['vector_store_size']}")
        print(f"   • 支持的服务: {', '.join(status['services_status'].keys())}")
        
        print("\n✅ B端RAG流水线功能验证完成!")
        print("📝 系统能够成功完成:")
        print("   • 新闻数据embedding生成")
        print("   • 向量相似度检索")
        print("   • RAG增强的新闻卡片生成") 
        print("   • 基于新闻上下文的智能对话")
        print("   • 多轮对话上下文管理")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n🏁 演示结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main()) 