#!/usr/bin/env python3
"""
认证功能测试脚本
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_user_registration():
    """测试用户注册功能"""
    print("🔍 测试用户注册功能...")
    
    try:
        from services.auth_service import auth_service
        from models.user import UserCreateRequest
        from core.database import init_database, close_database
        
        # 初始化数据库
        await init_database()
        
        # 创建测试用户数据
        test_user = UserCreateRequest(
            username="testuser123",
            email="test@example.com",
            password="testpassword123",
            nickname="测试用户"
        )
        
        # 测试注册
        result = await auth_service.create_user(test_user)
        
        print(f"注册结果: {result.status}")
        print(f"消息: {result.message}")
        print(f"用户ID: {result.user_id}")
        
        if result.status == "success":
            print("✅ 用户注册成功")
            
            # 测试登录
            from models.user import UserLoginRequest
            login_data = UserLoginRequest(
                username="testuser123",
                password="testpassword123"
            )
            
            login_result = await auth_service.login_user(login_data)
            print(f"登录结果: {login_result.status}")
            print(f"登录消息: {login_result.message}")
            
            if login_result.status == "success":
                print("✅ 用户登录成功")
                return True
            else:
                print("❌ 用户登录失败")
                return False
        else:
            print("❌ 用户注册失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False
    finally:
        await close_database()

async def main():
    """主测试函数"""
    print("🚀 认证功能测试")
    print("=" * 50)
    
    success = await test_user_registration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 认证功能测试通过！")
    else:
        print("⚠️  认证功能测试失败")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
