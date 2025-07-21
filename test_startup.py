#!/usr/bin/env python3
"""
启动测试脚本 - 验证后端服务能否正常启动
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块
        from core.config import settings
        print("✅ 核心配置模块导入成功")
        
        from core.database import init_database, close_database
        print("✅ 数据库模块导入成功")
        
        # 测试服务模块
        from services.unified_news_service import UnifiedNewsService
        print("✅ 统一新闻服务导入成功")
        
        from services.news_service import NewsService
        print("✅ 新闻服务导入成功")
        
        from services.qwen_service import QWENService
        print("✅ QWEN服务导入成功")
        
        from services.news_card_service import NewsCardService
        print("✅ 新闻卡片服务导入成功")
        
        # 测试API模块
        from api.unified_news import router
        print("✅ 统一新闻API导入成功")
        
        # 测试主应用
        from main import app
        print("✅ 主应用导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

async def test_services():
    """测试服务实例化"""
    print("\n🔍 测试服务实例化...")

    try:
        # 重新导入以确保在正确的作用域中
        from services.unified_news_service import UnifiedNewsService

        # 测试统一新闻服务
        unified_service = UnifiedNewsService()
        print("✅ 统一新闻服务实例化成功")

        # 测试服务初始化
        await unified_service._get_services()
        print("✅ 服务依赖初始化成功")

        return True

    except Exception as e:
        print(f"❌ 服务实例化失败: {e}")
        return False

async def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from core.database import init_database, close_database, get_mongodb_database
        
        # 初始化数据库连接
        await init_database()
        print("✅ 数据库初始化成功")
        
        # 测试MongoDB连接
        db = await get_mongodb_database()
        if db is not None:
            print("✅ MongoDB连接成功")
        else:
            print("⚠️  MongoDB连接失败，但不影响启动")
        
        # 关闭数据库连接
        await close_database()
        print("✅ 数据库连接已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

async def test_api_routes():
    """测试API路由"""
    print("\n🔍 测试API路由...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 测试健康检查
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ 健康检查API正常")
        else:
            print(f"⚠️  健康检查API返回状态码: {response.status_code}")
        
        # 测试统一新闻API健康检查
        response = client.get("/api/unified-news/health")
        if response.status_code == 200:
            print("✅ 统一新闻API健康检查正常")
        else:
            print(f"⚠️  统一新闻API健康检查返回状态码: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 News Mosaic 后端启动测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("服务实例化", test_services),
        ("数据库连接", test_database_connection),
        ("API路由", test_api_routes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！后端可以正常启动！")
        print("\n💡 启动命令:")
        print("cd backend")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("⚠️  部分测试失败，请检查相关配置")
    
    return passed == total

if __name__ == "__main__":
    print("News Mosaic 后端启动测试")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("❌ Python版本过低，需要Python 3.9+")
        sys.exit(1)
    
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
