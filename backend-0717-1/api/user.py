"""
用户管理 API 路由
提供用户注册、登录、会话管理等 HTTP 接口
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
import logging

from models.user import (
    UserCreateRequest, UserLoginRequest, UserSessionRequest, UserDeleteRequest,
    UserCreateResult, UserLoginResult, UserSessionResult, 
    UserDeleteResponse, SessionDeleteResponse, UserSessionsResponse
)
from services.auth_service import get_user_auth_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/auth/register", response_model=UserCreateResult)
async def register_user(user_data: UserCreateRequest):
    """
    用户注册 - 注册页面调用
    
    Args:
        user_data: 用户注册信息
        
    Returns:
        UserCreateResult: 注册结果
    """
    try:
        service = await get_user_auth_service()
        result = await service.create_user(user_data)
        
        # 检查是否创建成功
        if not result.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在或注册失败"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/auth/login", response_model=UserLoginResult)
async def login_user(login_data: UserLoginRequest):
    """
    用户登录 - 登录页面调用
    
    Args:
        login_data: 登录信息
        
    Returns:
        UserLoginResult: 登录结果，包含用户信息和会话列表
    """
    try:
        service = await get_user_auth_service()
        result = await service.login_user(login_data)
        
        # 检查登录是否成功
        if not result.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/sessions/create", response_model=UserSessionResult)
async def create_user_session(session_data: UserSessionRequest):
    """
    创建新会话 - 左侧栏"新建会话"按钮调用
    
    Args:
        session_data: 会话创建信息
        
    Returns:
        UserSessionResult: 会话创建结果
    """
    try:
        service = await get_user_auth_service()
        result = await service.create_session(session_data)
        
        # 检查会话是否创建成功
        if not result.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在或会话创建失败"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )


@router.get("/sessions/list/{user_id}", response_model=UserSessionsResponse)
async def get_user_sessions(user_id: str):
    """
    获取会话历史 - 左侧栏历史记录显示
    
    Args:
        user_id: 用户ID
        
    Returns:
        UserSessionsResponse: 用户会话列表
    """
    try:
        service = await get_user_auth_service()
        result = await service.get_user_sessions(user_id)
        
        # 检查是否有错误
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return UserSessionsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_user_session(session_id: str):
    """
    删除会话 - 左侧栏右键删除调用
    
    Args:
        session_id: 会话ID
        
    Returns:
        SessionDeleteResponse: 删除结果
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_session(session_id)
        
        # 转换为响应模型
        response = SessionDeleteResponse(**result)
        
        # 检查删除是否成功
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


@router.delete("/profile/delete/{user_id}", response_model=UserDeleteResponse)
async def delete_user_by_id(user_id: str):
    """
    管理员删除用户 - 系统管理调用（级联删除所有会话和新闻）
    
    Args:
        user_id: 用户ID
        
    Returns:
        UserDeleteResponse: 删除结果
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_user(user_id)
        
        # 转换为响应模型
        response = UserDeleteResponse(**result)
        
        # 检查删除是否成功
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.post("/profile/delete-account", response_model=UserDeleteResponse)
async def delete_user_by_credentials(user_data: UserDeleteRequest):
    """
    用户自删账号 - 用户信息框删除用户调用（需要密码确认）
    前端流程：显示用户名 → 用户输入密码确认 → 调用此接口删除
    
    Args:
        user_data: 用户删除请求信息（包含用户名和确认密码）
        
    Returns:
        UserDeleteResponse: 删除结果
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_user_by_credentials(
            user_data.username, 
            user_data.password
        )
        
        # 转换为响应模型
        response = UserDeleteResponse(**result)
        
        # 检查删除是否成功
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户账号失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户账号失败: {str(e)}"
        )
