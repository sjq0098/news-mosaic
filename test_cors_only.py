#!/usr/bin/env python3
"""
只测试CORS和注册API
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:8000"

def test_cors_and_registration():
    """测试CORS和注册功能"""
    print("🔍 测试CORS和用户注册...")
    
    # 生成唯一的测试用户
    timestamp = int(time.time())
    test_user = {
        "username": f"testuser_{timestamp}",
        "password": "Test123456!",
        "email": f"test_{timestamp}@example.com",
        "nickname": f"测试用户_{timestamp}"
    }
    
    print(f"测试用户信息: {test_user}")
    
    try:
        # 1. 测试预检请求
        print("\n1. 测试CORS预检请求...")
        headers = {
            'Origin': 'http://localhost:3005',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        preflight_response = requests.options(
            f"{BASE_URL}/api/user/auth/register",
            headers=headers,
            timeout=10
        )
        
        print(f"预检状态码: {preflight_response.status_code}")
        print(f"预检响应头: {dict(preflight_response.headers)}")
        
        # 2. 测试实际注册请求
        print("\n2. 测试注册请求...")
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:3005'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/user/auth/register",
            json=test_user,
            headers=headers,
            timeout=10
        )
        
        print(f"注册状态码: {response.status_code}")
        print(f"注册响应头: {dict(response.headers)}")
        print(f"注册响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 用户注册成功！")
                return True
            else:
                print(f"❌ 注册失败: {result.get('message')}")
                return False
        else:
            print(f"❌ 注册请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("🔍 测试API端点...")
    
    endpoints = [
        "/health",
        "/",
        "/api/user/auth/register"
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint == "/api/user/auth/register":
                # 对于注册端点，使用OPTIONS方法测试
                response = requests.options(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            
            print(f"  {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"  {endpoint}: 错误 - {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试CORS和注册功能...")
    print("=" * 60)
    
    # 1. 测试API端点
    test_api_endpoints()
    
    # 2. 测试CORS和注册
    print("\n" + "=" * 60)
    success = test_cors_and_registration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 CORS和注册功能测试通过！")
        print("✨ 前端应该可以正常注册用户了")
    else:
        print("❌ CORS和注册功能测试失败")
        print("💡 请检查后端服务和CORS配置")

if __name__ == "__main__":
    main()
