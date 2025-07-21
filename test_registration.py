#!/usr/bin/env python3
"""
测试用户注册功能
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3005"

def test_cors_preflight():
    """测试CORS预检请求"""
    print("🔍 测试CORS预检请求...")
    
    try:
        # 模拟浏览器的预检请求
        headers = {
            'Origin': FRONTEND_URL,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(
            f"{BASE_URL}/api/user/auth/register",
            headers=headers,
            timeout=5
        )
        
        print(f"预检请求状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 检查CORS头
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print(f"CORS头信息: {cors_headers}")
        
        if response.status_code == 200 and cors_headers['Access-Control-Allow-Origin']:
            print("✅ CORS预检请求成功")
            return True
        else:
            print("❌ CORS预检请求失败")
            return False
            
    except Exception as e:
        print(f"❌ CORS预检请求异常: {e}")
        return False

def test_user_registration():
    """测试用户注册"""
    print("\n👤 测试用户注册...")
    
    # 生成唯一的测试用户
    timestamp = int(time.time())
    test_user = {
        "username": f"testuser_{timestamp}",
        "password": "Test123456!",
        "email": f"test_{timestamp}@example.com",
        "nickname": f"测试用户_{timestamp}"
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': FRONTEND_URL
        }
        
        response = requests.post(
            f"{BASE_URL}/api/user/auth/register",
            json=test_user,
            headers=headers,
            timeout=10
        )
        
        print(f"注册请求状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 用户注册成功")
                print(f"   用户ID: {result.get('data', {}).get('user_id')}")
                print(f"   用户名: {result.get('data', {}).get('username')}")
                return True
            else:
                print(f"❌ 注册失败: {result.get('message')}")
                return False
        else:
            print(f"❌ 注册请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 注册请求异常: {e}")
        return False

def test_api_health():
    """测试API健康状态"""
    print("🔍 测试API健康状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

def test_frontend_access():
    """测试前端访问"""
    print("🌐 测试前端访问...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常")
            return True
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接前端服务: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试用户注册功能...")
    print("=" * 60)
    
    # 1. 检查服务状态
    backend_ok = test_api_health()
    frontend_ok = test_frontend_access()
    
    if not backend_ok:
        print("\n❌ 后端服务不可用，请先启动后端服务")
        return
    
    if not frontend_ok:
        print("\n❌ 前端服务不可用，请先启动前端服务")
        return
    
    # 2. 测试CORS配置
    cors_ok = test_cors_preflight()
    
    # 3. 测试用户注册
    if cors_ok:
        registration_ok = test_user_registration()
        
        print("\n" + "=" * 60)
        if registration_ok:
            print("🎉 用户注册功能测试通过！")
            print("✨ 现在可以正常注册用户了")
        else:
            print("❌ 用户注册功能测试失败")
    else:
        print("\n❌ CORS配置有问题，无法进行注册测试")
        print("💡 建议检查:")
        print("   1. 后端CORS_ORIGINS配置是否包含前端地址")
        print("   2. 后端服务是否重启以应用新配置")
    
    print("\n📝 测试信息:")
    print(f"   后端地址: {BASE_URL}")
    print(f"   前端地址: {FRONTEND_URL}")
    print(f"   注册接口: {BASE_URL}/api/user/auth/register")

if __name__ == "__main__":
    main()
