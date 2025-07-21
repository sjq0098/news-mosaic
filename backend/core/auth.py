"""
认证中间件和依赖注入
提供JWT认证、用户权限验证等功能
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from services.auth_service import auth_service
from services.user_service import user_service
from models.user import UserResponse
from core.config import settings


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户（可选）
    如果没有提供token或token无效，返回None而不抛出异常
    """
    if not credentials:
        return None
    
    try:
        # 验证token
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            return None
        
        # 获取用户信息
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            return None
        
        # 检查用户状态
        if user.get("status") != "active":
            return None
        
        return {
            "id": user["_id"],
            "username": user["username"],
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "nickname": user.get("nickname"),
            "avatar_url": user.get("avatar_url"),
            "preferences": user.get("preferences", {})
        }
        
    except Exception as e:
        logger.warning(f"获取当前用户失败: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前用户（必需）
    如果没有提供token或token无效，抛出401异常
    """
    # 演示模式：返回默认用户
    if settings.DEMO_MODE:
        return {
            "id": "demo_user",
            "user_id": "demo_user",
            "username": "demo_user",
            "email": "demo@example.com",
            "role": "user",
            "nickname": "演示用户",
            "avatar_url": None,
            "preferences": {}
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 验证token
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户信息
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌中缺少用户信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user["_id"],
            "username": user["username"],
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "nickname": user.get("nickname"),
            "avatar_url": user.get("avatar_url"),
            "preferences": user.get("preferences", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前活跃用户"""
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前管理员用户"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_permissions(*permissions: str):
    """
    权限装饰器工厂
    用于创建需要特定权限的依赖函数
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "user")
        
        # 超级管理员拥有所有权限
        if user_role == "super_admin":
            return current_user
        
        # 检查权限
        role_permissions = {
            "admin": ["read", "write", "delete", "manage_users"],
            "user": ["read", "write"]
        }
        
        user_permissions = role_permissions.get(user_role, [])
        
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}"
                )
        
        return current_user
    
    return permission_checker


# 常用权限依赖
require_read = require_permissions("read")
require_write = require_permissions("write")
require_delete = require_permissions("delete")
require_manage_users = require_permissions("manage_users")


async def verify_user_ownership(
    resource_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """
    验证用户是否拥有资源
    管理员可以访问所有资源
    """
    if current_user.get("role") in ["admin", "super_admin"]:
        return True
    
    return current_user.get("id") == resource_user_id


class AuthenticationError(Exception):
    """认证错误"""
    pass


class AuthorizationError(Exception):
    """授权错误"""
    pass
