"""
用户管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from models.user import (
    UserResponse, UserCreate, UserUpdate, UserLogin, 
    UserPasswordChange, UserPreferences
)
from services.user_service import UserService
from services.auth_service import AuthService
from core.cache import cache, CacheKeys

router = APIRouter()
security = HTTPBearer()

def get_user_service() -> UserService:
    """获取用户服务实例"""
    return UserService()

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """获取当前用户（JWT认证）"""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败"
        )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户注册"""
    
    try:
        # 使用 auth_service 来创建用户（包含密码处理）
        user = await auth_service.create_user_with_password(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.nickname
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login")
async def login_user(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户登录"""
    
    try:
        # 验证用户凭据
        user = await auth_service.authenticate_user(
            login_data.username, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成访问令牌
        access_token = await auth_service.create_access_token(user.id)
        
        # 更新最后登录时间
        await user_service.update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户资料"""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户资料"""
    
    try:
        updated_user = await user_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 清除用户缓存
        await cache.delete(f"{CacheKeys.USER_SESSION}{current_user.id}")
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """修改密码"""
    
    try:
        # 验证旧密码
        is_valid = await auth_service.verify_password(
            current_user.id, 
            password_data.old_password
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 更新密码
        success = await auth_service.change_password(
            current_user.id, 
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码修改失败"
            )
        
        return {"message": "密码修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户偏好设置"""
    
    cache_key = f"{CacheKeys.USER_PREFERENCES}{current_user.id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    preferences = await user_service.get_user_preferences(current_user.id)
    await cache.set(cache_key, preferences.dict(), expire=3600)  # 1小时缓存
    
    return preferences


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences_data: UserPreferences,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户偏好设置"""
    
    try:
        preferences = await user_service.update_user_preferences(
            current_user.id, 
            preferences_data
        )
        
        # 清除缓存
        await cache.delete(f"{CacheKeys.USER_PREFERENCES}{current_user.id}")
        
        return preferences
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"偏好设置更新失败: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户统计信息"""
    
    cache_key = f"{CacheKeys.USER_SESSION}stats:{current_user.id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    stats = await user_service.get_user_stats(current_user.id)
    await cache.set(cache_key, stats, expire=1800)  # 30分钟缓存
    
    return stats


@router.post("/logout")
async def logout_user(
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户登出"""
    
    try:
        # 将令牌加入黑名单
        await auth_service.revoke_token(current_user.id)
        
        # 清除用户相关缓存
        await cache.flush_pattern(f"{CacheKeys.USER_SESSION}{current_user.id}*")
        await cache.flush_pattern(f"{CacheKeys.USER_PREFERENCES}{current_user.id}*")
        
        return {"message": "登出成功"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.delete("/account")
async def delete_user_account(
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """删除用户账户"""
    
    try:
        success = await user_service.delete_user(current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="账户删除失败"
            )
        
        # 清除所有相关缓存
        await cache.flush_pattern(f"*{current_user.id}*")
        
        return {"message": "账户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"账户删除失败: {str(e)}"
        )


# 管理员路由
@router.get("/admin/users")
async def get_all_users(
    page: int = 1,
    size: int = 20,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取所有用户（管理员功能）"""
    
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    users = await user_service.get_all_users(page=page, size=size)
    return users


@router.put("/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status: str,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户状态（管理员功能）"""
    
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    success = await user_service.update_user_status(user_id, status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": f"用户状态已更新为: {status}"}