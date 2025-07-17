"""
用户认证公共接口函数 - 保持向后兼容
这些函数保持与原始 user_auth_service.py 中的公共接口完全相同
"""

from typing import Dict, Any, Optional
import logging

from models.user import UserCreateResult, UserLoginResult, UserSessionResult
from services.auth_service import get_user_auth_service

logger = logging.getLogger(__name__)


async def create_user_account(
    username: str,
    password: str
) -> UserCreateResult:
    """
    创建用户账号
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        UserCreateResult: 创建结果
    """
    try:
        service = await get_user_auth_service()
        from models.user import UserCreateRequest
        request = UserCreateRequest(
            username=username,
            password=password
        )
        return await service.create_user(request)
        
    except Exception as e:
        logger.error(f"创建用户接口错误: {str(e)}")
        return UserCreateResult(
            user_id="",
            username=username
        )


async def user_login(username: str, password: str) -> UserLoginResult:
    """
    用户登录
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        UserLoginResult: 登录结果，包含用户信息和会话列表
    """
    try:
        service = await get_user_auth_service()
        from models.user import UserLoginRequest
        request = UserLoginRequest(username=username, password=password)
        return await service.login_user(request)
        
    except Exception as e:
        logger.error(f"用户登录接口错误: {str(e)}")
        return UserLoginResult(
            user_id="",
            username=username,
            sessions=[]
        )


async def create_user_session(user_id: str, session_name: Optional[str] = None) -> UserSessionResult:
    """
    创建用户会话
    
    Args:
        user_id: 用户ID
        session_name: 会话名称（可选）
        
    Returns:
        UserSessionResult: 创建结果
    """
    try:
        service = await get_user_auth_service()
        from models.user import UserSessionRequest
        request = UserSessionRequest(user_id=user_id, session_name=session_name)
        return await service.create_session(request)
        
    except Exception as e:
        logger.error(f"创建会话接口错误: {str(e)}")
        return UserSessionResult(
            session_id="",
            session_name=""
        )


async def delete_user_account(user_id: str) -> Dict[str, Any]:
    """
    删除用户账号
    级联删除用户的所有会话
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 删除结果
    """
    service = await get_user_auth_service()
    return await service.delete_user(user_id)


async def get_user_sessions_list(user_id: str) -> Dict[str, Any]:
    """
    获取用户会话列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 会话列表和统计信息
    """
    service = await get_user_auth_service()
    return await service.get_user_sessions(user_id)


async def delete_user_session(session_id: str) -> Dict[str, Any]:
    """
    删除用户会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        Dict: 删除结果
    """
    service = await get_user_auth_service()
    return await service.delete_session(session_id)


async def delete_user_by_credentials(username: str, password: str) -> Dict[str, Any]:
    """
    根据用户名和密码删除用户
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        Dict: 删除结果
    """
    service = await get_user_auth_service()
    return await service.delete_user_by_credentials(username, password)
