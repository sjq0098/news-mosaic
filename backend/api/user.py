"""
用户管理 API 路由
提供用户注册、登录、会话管理等 HTTP 接口
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from loguru import logger

from models.user import (
    UserCreateRequest, UserLoginRequest, UserSessionRequest, UserDeleteRequest,
    UserCreateResult, UserLoginResult, UserSessionResult, 
    UserDeleteResponse, SessionDeleteResponse, UserSessionsResponse,
    UserResponse, UserUpdate, UserPreferences, UserPasswordChange
)
from services.auth_service import auth_service
from services.user_service import user_service
from core.auth import get_current_user, get_current_user_optional

router = APIRouter()


# ==================== 认证相关接口 ====================

@router.post("/auth/register", response_model=UserCreateResult)
async def register_user(user_data: UserCreateRequest):
    """
    用户注册
    """
    try:
        result = await auth_service.create_user(user_data)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
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
    用户登录
    """
    try:
        result = await auth_service.login_user(login_data)
        
        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
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


@router.post("/auth/refresh")
async def refresh_token(request: dict):
    """
    刷新访问令牌
    """
    try:
        refresh_token = request.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少刷新令牌"
            )

        payload = auth_service.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 生成新的访问令牌
        token_data = {
            "sub": payload["sub"],
            "username": payload["username"],
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
        
        new_access_token = auth_service.create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败"
        )


# ==================== 用户信息管理接口 ====================

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取当前用户档案
    """
    try:
        user_profile = await user_service.get_user_profile(current_user["id"])
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return user_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户档案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户档案失败"
        )


@router.put("/profile", response_model=Dict[str, str])
async def update_user_profile(
    update_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新用户档案
    """
    try:
        success = await user_service.update_user_profile(current_user["id"], update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新用户档案失败"
            )
        
        return {"message": "用户档案更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户档案失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户档案失败"
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取用户偏好设置
    """
    try:
        preferences = await user_service.get_user_preferences(current_user["id"])
        if not preferences:
            # 返回默认偏好设置
            preferences = UserPreferences()
        
        return preferences
        
    except Exception as e:
        logger.error(f"获取用户偏好失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户偏好失败"
        )


@router.put("/preferences", response_model=Dict[str, str])
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新用户偏好设置
    """
    try:
        success = await user_service.update_user_preferences(current_user["id"], preferences)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新用户偏好失败"
            )
        
        return {"message": "用户偏好更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户偏好失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户偏好失败"
        )


@router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    password_data: UserPasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    修改密码
    """
    try:
        success = await user_service.change_user_password(
            current_user["id"],
            password_data.old_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码修改失败，请检查旧密码是否正确"
            )
        
        return {"message": "密码修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )


@router.get("/activity", response_model=Dict[str, Any])
async def get_user_activity(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取用户活动摘要
    """
    try:
        activity = await user_service.get_user_activity_summary(current_user["id"])
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户活动数据不存在"
            )
        
        return activity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户活动失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户活动失败"
        )


# ==================== 个性化功能接口 ====================

@router.get("/personalization/news-query")
async def get_personalized_news_query(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取个性化新闻查询参数
    """
    try:
        from services.personalization_service import personalization_service
        query_params = await personalization_service.get_personalized_news_query(current_user["id"])
        return {"status": "success", "data": query_params}

    except Exception as e:
        logger.error(f"获取个性化查询参数失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取个性化查询参数失败"
        )


@router.post("/personalization/interaction")
async def record_user_interaction(
    interaction_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_optional)
):
    """
    记录用户交互行为
    """
    if not current_user:
        return {"message": "未登录用户，跳过记录"}

    try:
        from services.personalization_service import personalization_service
        success = await personalization_service.record_user_interaction(
            current_user["id"],
            interaction_data.get("type"),
            interaction_data.get("content_id"),
            interaction_data.get("metadata", {})
        )

        if success:
            return {"message": "交互记录成功"}
        else:
            return {"message": "交互记录失败"}

    except Exception as e:
        logger.warning(f"记录用户交互失败: {str(e)}")
        return {"message": "交互记录失败"}


@router.get("/personalization/history")
async def get_user_reading_history(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户阅读历史
    """
    try:
        from services.personalization_service import personalization_service
        history = await personalization_service.get_user_reading_history(current_user["id"], limit)
        return {"status": "success", "data": history}

    except Exception as e:
        logger.error(f"获取用户阅读历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取阅读历史失败"
        )


@router.get("/personalization/trending")
async def get_trending_topics(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """
    获取热门话题（个性化）
    """
    try:
        from services.personalization_service import personalization_service
        user_id = current_user["id"] if current_user else None
        topics = await personalization_service.get_trending_topics(user_id)
        return {"status": "success", "data": topics}

    except Exception as e:
        logger.error(f"获取热门话题失败: {str(e)}")
        return {"status": "error", "data": ["科技", "财经", "社会", "国际"]}


@router.get("/personalization/recommended-keywords")
async def get_recommended_keywords(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取推荐关键词
    """
    try:
        from services.personalization_service import personalization_service
        keywords = await personalization_service.get_recommended_keywords(current_user["id"])
        return {"status": "success", "data": keywords}

    except Exception as e:
        logger.error(f"获取推荐关键词失败: {str(e)}")
        return {"status": "error", "data": []}


# ==================== 搜索历史接口 ====================

@router.get("/search-history")
async def get_user_search_history(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户搜索历史
    """
    try:
        from core.database import get_mongodb_database, Collections

        db = await get_mongodb_database()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库连接失败"
            )

        # 查询用户搜索历史
        cursor = db[Collections.SEARCH_HISTORY].find(
            {"user_id": current_user["id"]}
        ).sort("timestamp", -1).limit(limit)

        history = []
        async for record in cursor:
            history.append({
                "_id": str(record["_id"]),
                "query": record["query"],
                "timestamp": record["timestamp"],
                "results_count": record.get("results_count", 0),
                "cards_generated": record.get("cards_generated", 0)
            })

        return {"status": "success", "data": history}

    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取搜索历史失败"
        )


@router.post("/search-history")
async def add_search_record(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    添加搜索记录
    """
    try:
        from core.database import get_mongodb_database, Collections
        from datetime import datetime
        import uuid

        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="搜索查询不能为空"
            )

        db = await get_mongodb_database()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库连接失败"
            )

        # 创建搜索记录
        search_record = {
            "_id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "query": query,
            "timestamp": datetime.utcnow(),
            "metadata": request.get("metadata", {})
        }

        # 检查是否已存在相同查询，如果存在则更新时间戳
        existing = await db[Collections.SEARCH_HISTORY].find_one({
            "user_id": current_user["id"],
            "query": query
        })

        if existing:
            # 更新现有记录的时间戳
            await db[Collections.SEARCH_HISTORY].update_one(
                {"_id": existing["_id"]},
                {"$set": {"timestamp": datetime.utcnow()}}
            )
            record_id = str(existing["_id"])
        else:
            # 插入新记录
            await db[Collections.SEARCH_HISTORY].insert_one(search_record)
            record_id = search_record["_id"]

        return {
            "status": "success",
            "message": "搜索记录已保存",
            "record_id": record_id
        }

    except Exception as e:
        logger.error(f"添加搜索记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加搜索记录失败"
        )


@router.delete("/search-history/{record_id}")
async def delete_search_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除单条搜索记录
    """
    try:
        from core.database import get_mongodb_database, Collections

        db = await get_mongodb_database()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库连接失败"
            )

        # 删除指定的搜索记录
        result = await db[Collections.SEARCH_HISTORY].delete_one({
            "_id": record_id,
            "user_id": current_user["id"]
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="搜索记录不存在"
            )

        return {"status": "success", "message": "搜索记录已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除搜索记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除搜索记录失败"
        )


@router.delete("/search-history")
async def clear_search_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    清空用户搜索历史
    """
    try:
        from core.database import get_mongodb_database, Collections

        db = await get_mongodb_database()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库连接失败"
            )

        # 删除用户的所有搜索记录
        result = await db[Collections.SEARCH_HISTORY].delete_many({
            "user_id": current_user["id"]
        })

        return {
            "status": "success",
            "message": f"已清空 {result.deleted_count} 条搜索记录"
        }

    except Exception as e:
        logger.error(f"清空搜索历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清空搜索历史失败"
        )


# ==================== 统计和工具接口 ====================

@router.post("/stats/increment/{stat_type}")
async def increment_user_stat(
    stat_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user_optional)
):
    """
    增加用户统计数据（可选认证）
    """
    if not current_user:
        return {"message": "未登录用户，跳过统计"}

    try:
        await user_service.increment_user_stats(current_user["id"], stat_type)
        return {"message": f"{stat_type} 统计已更新"}

    except Exception as e:
        logger.warning(f"更新用户统计失败: {str(e)}")
        return {"message": "统计更新失败"}


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """
    用户服务健康检查
    """
    return {
        "status": "healthy",
        "service": "user-api",
        "timestamp": "2024-01-01T00:00:00Z"
    }
