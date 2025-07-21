"""
用户记忆管理 API
提供用户行为记录、兴趣学习、个性化推荐等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from loguru import logger

from core.auth import get_current_user
from services.user_memory_service import (
    UserMemoryService,
    UserMemoryRequest,
    UserMemoryResponse,
    PersonalizationRequest,
    PersonalizationResponse,
    get_user_memory_service
)

router = APIRouter(prefix="/api/user-memory", tags=["用户记忆管理"])


@router.post("/record-behavior", response_model=UserMemoryResponse)
async def record_user_behavior(
    request: UserMemoryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    记录用户行为并更新记忆
    
    支持的行为类型：
    - search: 搜索行为
    - click: 点击行为
    - like: 点赞行为
    - share: 分享行为
    - comment: 评论行为
    - bookmark: 收藏行为
    
    Args:
        request: 用户记忆请求
        current_user: 当前用户信息
        memory_service: 用户记忆服务
        
    Returns:
        UserMemoryResponse: 记录结果
    """
    try:
        # 设置用户ID
        request.user_id = current_user.get("user_id", "anonymous")
        
        logger.info(f"记录用户行为: {request.user_id} - {request.action}")
        
        # 记录行为
        response = await memory_service.record_user_behavior(request)
        
        logger.info(f"用户行为记录完成: {response.success}")
        
        return response
        
    except Exception as e:
        logger.error(f"记录用户行为失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录用户行为失败: {str(e)}"
        )


@router.post("/personalization", response_model=PersonalizationResponse)
async def get_personalized_content(
    request: PersonalizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    获取个性化内容推荐
    
    Args:
        request: 个性化请求
        current_user: 当前用户信息
        memory_service: 用户记忆服务
        
    Returns:
        PersonalizationResponse: 个性化推荐结果
    """
    try:
        # 设置用户ID
        request.user_id = current_user.get("user_id", "anonymous")
        
        logger.info(f"获取个性化内容: {request.user_id}")
        
        # 获取个性化推荐
        response = await memory_service.get_personalized_content(request)
        
        logger.info(f"个性化内容获取完成: {response.success}")
        
        return response
        
    except Exception as e:
        logger.error(f"获取个性化内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个性化内容失败: {str(e)}"
        )


@router.post("/quick-record")
async def quick_record_behavior(
    action: str,
    content: str,
    target_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    快速记录用户行为
    
    Args:
        action: 行为类型
        content: 内容
        target_id: 目标ID（可选）
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        request = UserMemoryRequest(
            user_id=current_user.get("user_id", "anonymous"),
            action=action,
            content=content,
            metadata={"target_id": target_id} if target_id else {}
        )
        
        response = await memory_service.record_user_behavior(request)
        
        return {
            "success": response.success,
            "message": response.message,
            "interests_updated": response.interests_updated,
            "personalization_score": response.personalization_score
        }
        
    except Exception as e:
        logger.error(f"快速记录行为失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速记录行为失败: {str(e)}"
        )


@router.get("/interest-profile")
async def get_user_interest_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    获取用户兴趣档案
    
    Args:
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 获取兴趣档案
        profile = await memory_service._get_user_interest_profile(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"获取用户兴趣档案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户兴趣档案失败: {str(e)}"
        )


@router.get("/recommendations")
async def get_user_recommendations(
    content_type: str = "news",
    max_count: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    获取用户推荐内容
    
    Args:
        content_type: 内容类型
        max_count: 最大数量
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        request = PersonalizationRequest(
            user_id=current_user.get("user_id", "anonymous"),
            content_type=content_type,
            max_recommendations=max_count
        )
        
        response = await memory_service.get_personalized_content(request)
        
        return {
            "success": response.success,
            "recommendations": response.recommendations,
            "confidence_score": response.confidence_score
        }
        
    except Exception as e:
        logger.error(f"获取用户推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户推荐失败: {str(e)}"
        )


@router.get("/personalized-queries")
async def get_personalized_queries(
    base_query: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    获取个性化查询建议
    
    Args:
        base_query: 基础查询（可选）
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 生成个性化查询
        queries = await memory_service._generate_personalized_queries(user_id, base_query)
        
        return {
            "success": True,
            "user_id": user_id,
            "base_query": base_query,
            "personalized_queries": queries
        }
        
    except Exception as e:
        logger.error(f"获取个性化查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个性化查询失败: {str(e)}"
        )


@router.delete("/clear-memory")
async def clear_user_memory(
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    清除用户记忆数据
    
    Args:
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 清除用户偏好
        await memory_service.db[memory_service.db.Collections.USER_PREFERENCES].delete_many({
            "user_id": user_id
        })
        
        # 清除用户行为记录
        await memory_service.db[memory_service.db.Collections.API_LOGS].delete_many({
            "user_id": user_id
        })
        
        return {
            "success": True,
            "message": "用户记忆数据已清除",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"清除用户记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除用户记忆失败: {str(e)}"
        )


@router.get("/analytics")
async def get_user_memory_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: UserMemoryService = Depends(get_user_memory_service)
):
    """
    获取用户记忆分析数据
    
    Args:
        current_user: 当前用户
        memory_service: 记忆服务
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        # 获取用户行为统计
        behavior_stats = {}
        for action in memory_service.behavior_weights.keys():
            count = await memory_service.db[memory_service.db.Collections.API_LOGS].count_documents({
                "user_id": user_id,
                "action": action
            })
            behavior_stats[action] = count
        
        # 获取兴趣档案
        profile = await memory_service._get_user_interest_profile(user_id)
        
        # 计算个性化分数
        personalization_score = await memory_service._calculate_personalization_score(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "behavior_stats": behavior_stats,
            "interest_profile": profile,
            "personalization_score": personalization_score,
            "total_behaviors": sum(behavior_stats.values())
        }
        
    except Exception as e:
        logger.error(f"获取用户记忆分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户记忆分析失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "user-memory-service",
        "version": "1.0.0",
        "features": [
            "behavior_recording",
            "interest_learning",
            "personalized_recommendations",
            "memory_analytics",
            "query_personalization"
        ]
    }
