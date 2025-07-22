#!/usr/bin/env python3
"""
测试新闻搜索功能
"""

import asyncio
import aiohttp
import json
import time

async def test_news_search():
    """测试新闻搜索API"""
    
    print("🧪 测试新闻搜索功能...")
    
    # 测试数据
    test_data = {
        "query": "金融科技",
        "num_results": 5,
        "enable_storage": True,
        "enable_vectorization": True,
        "enable_ai_analysis": True,
        "enable_card_generation": True,
        "enable_sentiment_analysis": True,
        "enable_user_memory": False,
        "max_cards": 5,
        "personalization_level": 0.5
    }
    
    url = "http://localhost:8000/api/news-pipeline/process"
    
    print(f"📤 发送请求到: {url}")
    print(f"📋 请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            print("⏱️  开始请求...")
            start_time = time.time()
            
            async with session.post(
                url, 
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=180)  # 3分钟超时
            ) as response:
                elapsed_time = time.time() - start_time
                
                print(f"📊 响应状态: {response.status}")
                print(f"⏱️  请求耗时: {elapsed_time:.2f}秒")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ 请求成功！")
                    print(f"📝 响应数据:")
                    print(json.dumps(result, ensure_ascii=False, indent=2)[:1000] + "...")
                    
                    # 检查关键字段
                    if result.get("success"):
                        print("✅ 处理成功")
                        if "news_list" in result:
                            print(f"📰 获取新闻数量: {len(result['news_list'])}")
                        if "ai_analysis" in result:
                            print("🤖 AI分析已生成")
                        if "cards" in result:
                            print(f"🎴 生成卡片数量: {len(result['cards'])}")
                    else:
                        print(f"❌ 处理失败: {result.get('message', '未知错误')}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 请求失败: {response.status}")
                    print(f"📄 错误信息: {error_text[:500]}...")
                    
    except asyncio.TimeoutError:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

async def test_simple_search():
    """测试简单搜索"""
    
    print("\n🔍 测试简单搜索...")
    
    test_data = {
        "query": "人工智能",
        "num_results": 3,
        "enable_storage": False,
        "enable_vectorization": False,
        "enable_ai_analysis": False,
        "enable_card_generation": False,
        "enable_sentiment_analysis": False,
        "enable_user_memory": False
    }
    
    url = "http://localhost:8000/api/news-pipeline/process"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                print(f"📊 响应状态: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ 简单搜索成功！")
                    
                    if result.get("success") and "news_list" in result:
                        news_count = len(result['news_list'])
                        print(f"📰 获取新闻数量: {news_count}")
                        
                        # 显示第一条新闻
                        if news_count > 0:
                            first_news = result['news_list'][0]
                            print(f"📄 第一条新闻标题: {first_news.get('title', 'N/A')}")
                            print(f"📄 新闻来源: {first_news.get('source', 'N/A')}")
                    else:
                        print(f"❌ 搜索失败: {result.get('message', '未知错误')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 请求失败: {response.status} - {error_text[:200]}...")
                    
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

async def test_health_check():
    """测试健康检查"""
    
    print("\n🏥 测试健康检查...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                print(f"📊 健康检查状态: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 服务健康: {result}")
                else:
                    print(f"❌ 服务异常: {response.status}")
                    
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")

async def main():
    """主函数"""
    print("🚀 新闻搜索功能测试开始")
    print("="*60)
    
    # 先测试健康检查
    await test_health_check()
    
    # 测试简单搜索
    await test_simple_search()
    
    # 测试完整搜索
    await test_news_search()
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("\n💡 提示：")
    print("   - 如果简单搜索成功，说明基础功能正常")
    print("   - 如果完整搜索超时，可能是AI分析或向量化耗时较长")
    print("   - 可以在前端尝试搜索，应该能看到结果")

if __name__ == "__main__":
    asyncio.run(main())
