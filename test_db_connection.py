#!/usr/bin/env python3
"""
测试数据库连接和数据查询
"""

import asyncio
import sys
sys.path.append("backend")

from core.database import init_database, get_mongodb_database, Collections

async def test_database():
    """测试数据库连接和查询"""
    print("🔍 测试数据库连接...")
    
    try:
        # 初始化数据库
        await init_database()
        print("✅ 数据库初始化成功")
        
        # 获取数据库实例
        db = await get_mongodb_database()
        if db is None:
            print("❌ 数据库连接为空")
            return
        
        print("✅ 数据库连接获取成功")
        
        # 查询新闻集合
        news_collection = db[Collections.NEWS]
        
        # 统计总数
        total_count = await news_collection.count_documents({})
        print(f"📊 新闻总数: {total_count}")
        
        if total_count > 0:
            # 获取最新的几条记录
            latest_news = await news_collection.find().sort("created_at", -1).limit(3).to_list(length=3)
            
            print(f"\n📰 最新的3条新闻:")
            for i, news in enumerate(latest_news, 1):
                print(f"  {i}. ID: {news.get('_id', 'N/A')}")
                print(f"     标题: {news.get('title', 'N/A')}")
                print(f"     来源: {news.get('source', 'N/A')}")
                print(f"     创建时间: {news.get('created_at', 'N/A')}")
                print()
            
            # 测试查询特定ID
            test_id = latest_news[0]['_id']
            print(f"🔍 测试查询特定ID: {test_id}")
            
            found_news = await news_collection.find_one({"_id": test_id})
            if found_news:
                print("✅ 查询成功")
                print(f"   标题: {found_news.get('title', 'N/A')}")
            else:
                print("❌ 查询失败")
        else:
            print("⚠️ 数据库中没有新闻记录")
        
    except Exception as e:
        print(f"💥 数据库测试异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_database())
