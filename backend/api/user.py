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

router = APIRouter()
logger = logging.getLogger(__name__)

# 临时解决方案：创建简化的认证服务
class SimpleAuthService:
    """简化的认证服务，临时用于启动"""
    
    async def create_user(self, user_data):
        return UserCreateResult(
            status="success",
            message="用户创建成功（模拟）",
            user_id="temp_user_id"
        )
    
    async def login_user(self, login_data):
        return UserLoginResult(
            status="success", 
            message="登录成功（模拟）",
            user_id="temp_user_id",
            username=login_data.username,
            sessions=[]
        )
    
    async def create_session(self, session_data):
        return UserSessionResult(
            status="success",
            message="会话创建成功（模拟）", 
            session_id="temp_session_id",
            session_name="临时会话"
        )
    
    async def get_user_sessions(self, user_id):
        return {
            "user_id": user_id,
            "sessions": [],
            "session_count": 0,
            "status": "success"
        }
    
    async def delete_session(self, session_id):
        return {
            "status": "success",
            "message": "会话删除成功（模拟）",
            "deleted_news": 0
        }
    
    async def delete_user(self, user_id):
        return {
            "status": "success", 
            "message": "用户删除成功（模拟）",
            "deleted_sessions": 0,
            "deleted_news": 0
        }
    
    async def delete_user_by_credentials(self, username, password):
        return {
            "status": "success",
            "message": "用户账号删除成功（模拟）",
            "deleted_sessions": 0,
            "deleted_news": 0
        }

async def get_user_auth_service():
    """获取简化的认证服务"""
    return SimpleAuthService()


@router.post("/auth/register", response_model=UserCreateResult)
async def register_user(user_data: UserCreateRequest):
    """
    用户注册 - 注册页面调用
    """
    try:
        service = await get_user_auth_service()
        result = await service.create_user(user_data)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.login_user(login_data)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.create_session(session_data)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.get_user_sessions(user_id)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_session(session_id)
        
        response = SessionDeleteResponse(**result)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_user(user_id)
        
        response = UserDeleteResponse(**result)
        
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
    """
    try:
        service = await get_user_auth_service()
        result = await service.delete_user_by_credentials(
            user_data.username, 
            user_data.password
        )
        
        response = UserDeleteResponse(**result)
        
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


@router.get("/interests/{user_id}")
async def get_user_interests(user_id: str):
    """
    获取用户兴趣列表
    """
    try:
        from services.user_interest_service import get_user_interests
        
        interests = await get_user_interests(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "interests": interests or [],
            "count": len(interests) if interests else 0
        }
        
    except Exception as e:
        logger.error(f"获取用户兴趣失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户兴趣失败: {str(e)}"
        )