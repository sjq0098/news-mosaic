#!/usr/bin/env python3
"""
集成测试脚本 - 验证项目重构后的功能
"""

import asyncio
import httpx
import json
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "test_user",
    "email": "test@example.com", 
    "password": "test123456"
}

class IntegrationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.user_id = None
    
    async def test_health_check(self):
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    async def test_user_registration(self):
        """测试用户注册"""
        print("🔍 测试用户注册...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/user/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    print("✅ 用户注册成功")
                    return True
                else:
                    print(f"❌ 用户注册失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 用户注册失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 用户注册异常: {e}")
            return False
    
    async def test_user_login(self):
        """测试用户登录"""
        print("🔍 测试用户登录...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/user/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.token = data.get("access_token")
                    self.user_id = data.get("user_id")
                    print("✅ 用户登录成功")
                    return True
                else:
                    print(f"❌ 用户登录失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 用户登录失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 用户登录异常: {e}")
            return False
    
    async def test_unified_news_service(self):
        """测试统一新闻服务"""
        print("🔍 测试统一新闻服务...")
        
        if not self.token:
            print("❌ 需要先登录")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # 测试健康检查
            response = await self.client.get(
                f"{BASE_URL}/api/unified-news/health",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ 统一新闻服务健康检查通过")
            else:
                print(f"❌ 统一新闻服务健康检查失败: {response.status_code}")
                return False
            
            # 测试快速搜索
            response = await self.client.post(
                f"{BASE_URL}/api/unified-news/quick-search",
                params={"query": "人工智能"},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 快速搜索成功: 找到 {data.get('total_found', 0)} 条新闻")
                    return True
                else:
                    print(f"❌ 快速搜索失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 快速搜索失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 统一新闻服务测试异常: {e}")
            return False
    
    async def test_news_search(self):
        """测试新闻搜索"""
        print("🔍 测试传统新闻搜索...")
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/news/search",
                params={
                    "query": "科技新闻",
                    "num_results": 5,
                    "language": "zh-cn",
                    "country": "cn"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ 传统新闻搜索成功")
                    return True
                else:
                    print(f"❌ 传统新闻搜索失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ 传统新闻搜索失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 传统新闻搜索异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始集成测试...")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("用户注册", self.test_user_registration),
            ("用户登录", self.test_user_login),
            ("统一新闻服务", self.test_unified_news_service),
            ("传统新闻搜索", self.test_news_search),
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
            print("🎉 所有测试通过！项目重构成功！")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        
        await self.client.aclose()

async def main():
    """主函数"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("News Mosaic 项目集成测试")
    print("=" * 50)
    asyncio.run(main())
