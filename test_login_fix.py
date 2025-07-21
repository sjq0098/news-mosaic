#!/usr/bin/env python3
"""
测试登录修复
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_login_flow():
    """测试完整的登录流程"""
    print("🔍 测试完整登录流程...")
    
    try:
        from services.auth_service import auth_service
        from models.user import UserCreateRequest, UserLoginRequest
        from core.database import init_database, close_database
        
        # 初始化数据库
        await init_database()
        
        # 1. 创建测试用户
        print("1. 创建测试用户...")
        test_user = UserCreateRequest(
            username="logintest123",
            email="logintest@example.com",
            password="testpassword123",
            nickname="登录测试用户"
        )
        
        create_result = await auth_service.create_user(test_user)
        print(f"   创建结果: {create_result.status}")

        if create_result.status != "success":
            if "已存在" in create_result.message:
                print(f"   ℹ️  用户已存在，跳过创建: {create_result.message}")
            else:
                print(f"   ❌ 用户创建失败: {create_result.message}")
                return False
        
        # 2. 测试登录
        print("2. 测试用户登录...")
        login_data = UserLoginRequest(
            username="logintest123",
            password="testpassword123"
        )
        
        login_result = await auth_service.login_user(login_data)
        print(f"   登录结果: {login_result.status}")
        print(f"   用户ID: {login_result.user_id}")
        print(f"   访问令牌: {login_result.access_token[:20]}..." if login_result.access_token else "无")
        print(f"   刷新令牌: {login_result.refresh_token[:20]}..." if login_result.refresh_token else "无")
        
        if login_result.status != "success":
            print(f"   ❌ 登录失败: {login_result.message}")
            return False
        
        # 3. 测试token验证
        print("3. 测试token验证...")
        if login_result.access_token:
            payload = auth_service.verify_token(login_result.access_token)
            if payload:
                print(f"   ✅ Token验证成功: {payload.get('username')}")
            else:
                print("   ❌ Token验证失败")
                return False
        
        # 4. 测试获取用户信息
        print("4. 测试获取用户信息...")
        user_info = await auth_service.get_user_by_id(login_result.user_id)
        if user_info:
            print(f"   ✅ 用户信息获取成功: {user_info.get('username')}")
        else:
            print("   ❌ 用户信息获取失败")
            return False
        
        print("✅ 登录流程测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_database()

async def test_refresh_token():
    """测试刷新令牌功能"""
    print("\n🔍 测试刷新令牌功能...")
    
    try:
        from services.auth_service import auth_service
        from models.user import UserLoginRequest
        from core.database import init_database, close_database
        
        # 初始化数据库
        await init_database()
        
        # 登录获取令牌
        login_data = UserLoginRequest(
            username="logintest123",
            password="testpassword123"
        )
        
        login_result = await auth_service.login_user(login_data)
        if login_result.status != "success":
            print("   ❌ 登录失败，无法测试刷新令牌")
            return False
        
        # 验证刷新令牌
        if login_result.refresh_token:
            print("   测试刷新令牌验证...")
            refresh_payload = auth_service.verify_token(login_result.refresh_token)
            if refresh_payload and refresh_payload.get("type") == "refresh":
                print("   ✅ 刷新令牌验证成功")
                
                # 生成新的访问令牌
                token_data = {
                    "sub": refresh_payload["sub"],
                    "username": refresh_payload["username"],
                    "email": refresh_payload.get("email"),
                    "role": refresh_payload.get("role", "user")
                }
                
                new_access_token = auth_service.create_access_token(token_data)
                print(f"   ✅ 新访问令牌生成成功: {new_access_token[:20]}...")
                
                # 验证新令牌
                new_payload = auth_service.verify_token(new_access_token)
                if new_payload:
                    print("   ✅ 新访问令牌验证成功")
                    return True
                else:
                    print("   ❌ 新访问令牌验证失败")
                    return False
            else:
                print("   ❌ 刷新令牌验证失败")
                return False
        else:
            print("   ❌ 没有刷新令牌")
            return False
            
    except Exception as e:
        print(f"❌ 刷新令牌测试异常: {e}")
        return False
    finally:
        await close_database()

async def main():
    """主测试函数"""
    print("🚀 登录修复测试")
    print("=" * 50)
    
    # 测试登录流程
    login_success = await test_login_flow()
    
    # 测试刷新令牌
    refresh_success = await test_refresh_token()
    
    print("\n" + "=" * 50)
    if login_success and refresh_success:
        print("🎉 所有测试通过！登录功能正常")
    else:
        print("⚠️  部分测试失败")
        if not login_success:
            print("   - 登录流程测试失败")
        if not refresh_success:
            print("   - 刷新令牌测试失败")
    
    return login_success and refresh_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
