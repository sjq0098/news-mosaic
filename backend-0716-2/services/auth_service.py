"""
用户认证服务 - 核心业务逻辑
从原有的 user_auth_service.py 中提取的服务层实现
"""

import hashlib
import uuid
import secrets
from typing import Dict, Any, Optional
import logging
from bson import ObjectId

from core.config import settings
from core.database import get_mongodb_database, Collections
from models.user import (
    UserCreateRequest, UserLoginRequest, UserSessionRequest,
    UserCreateResult, UserLoginResult, UserSessionResult
)
from services.memory_mongo import SessionMemoryStore

logger = logging.getLogger(__name__)


class UserAuthService:
    """
    用户认证和会话管理服务
    
    核心功能：
    1. 用户注册/创建
    2. 用户登录认证
    3. 用户删除（级联删除会话）
    4. 会话管理
    5. 用户信息查询
    """
    
    def __init__(self):
        """初始化用户认证服务"""
        self.memory_store = SessionMemoryStore()
        logger.info("用户认证服务初始化完成")
    
    async def create_user(self, request: UserCreateRequest) -> UserCreateResult:
        """
        创建新用户
        
        Args:
            request: 用户创建请求
            
        Returns:
            UserCreateResult: 创建结果
        """
        logger.info(f"开始创建用户: {request.username}")
        
        try:
            db = await get_mongodb_database()
            if db is None:
                return UserCreateResult(
                    user_id="",
                    username=request.username
                )
            
            users_collection = db[Collections.USERS]
            
            # 检查用户名是否已存在
            existing_user = await users_collection.find_one({"username": request.username})
            if existing_user:
                return UserCreateResult(
                    user_id="",
                    username=request.username
                )
            
            # 生成密码哈希
            password_hash = self._hash_password(request.password)
            
            # 创建用户文档
            user_doc = {
                "username": request.username,
                "password_hash": password_hash
            }
            
            # 保存到数据库
            result = await users_collection.insert_one(user_doc)
            user_id = str(result.inserted_id)
            
            logger.info(f"用户创建成功: {request.username} (ID: {user_id})")
            
            return UserCreateResult(
                user_id=user_id,
                username=request.username
            )
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return UserCreateResult(
                user_id="",
                username=request.username
            )
    
    async def login_user(self, request: UserLoginRequest) -> UserLoginResult:
        """
        用户登录
        
        Args:
            request: 登录请求
            
        Returns:
            UserLoginResult: 登录结果，包含用户信息和会话列表
        """
        logger.info(f"用户登录请求: {request.username}")
        
        try:
            db = await get_mongodb_database()
            if db is None:
                return UserLoginResult(
                    user_id="",
                    username=request.username,
                    sessions=[]
                )
            
            users_collection = db[Collections.USERS]
            sessions_collection = db[Collections.USER_SESSIONS]
            
            # 查找用户
            user = await users_collection.find_one({"username": request.username})
            if not user:
                return UserLoginResult(
                    user_id="",
                    username=request.username,
                    sessions=[]
                )
            
            # 验证密码
            if not self._verify_password(request.password, user["password_hash"]):
                return UserLoginResult(
                    user_id="",
                    username=request.username,
                    sessions=[]
                )
            
            # 获取用户会话列表
            user_id_str = str(user["_id"])
            sessions = []
            async for session in sessions_collection.find({"user_id": user_id_str}):
                sessions.append({
                    "session_id": str(session["_id"]),
                    "session_name": session["session_name"]
                })
            
            logger.info(f"用户登录成功: {request.username} (ID: {user['_id']})")
            
            return UserLoginResult(
                user_id=str(user["_id"]),
                username=user["username"],
                sessions=sessions
            )
            
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            return UserLoginResult(
                user_id="",
                username=request.username,
                sessions=[]
            )
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        删除用户（级联删除所有会话和相关新闻）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 删除结果
        """
        logger.info(f"开始删除用户: {user_id}")
        
        try:
            db = await get_mongodb_database()
            if db is None:
                return {
                    "status": "error",
                    "message": "数据库连接失败",
                    "deleted_sessions": 0,
                    "deleted_news": 0
                }
            
            users_collection = db[Collections.USERS]
            sessions_collection = db[Collections.USER_SESSIONS]
            news_collection = db[Collections.NEWS]
            
            # 检查用户是否存在
            try:
                user_object_id = ObjectId(user_id)
                user = await users_collection.find_one({"_id": user_object_id})
            except Exception:
                return {
                    "status": "error",
                    "message": "用户ID格式错误",
                    "deleted_sessions": 0,
                    "deleted_news": 0
                }
            
            if not user:
                return {
                    "status": "error",
                    "message": "用户不存在",
                    "deleted_sessions": 0,
                    "deleted_news": 0
                }
            
            # 获取用户的所有会话ID
            session_ids = []
            async for session in sessions_collection.find({"user_id": user_id}):
                session_ids.append(str(session["_id"]))
            
            # 级联删除所有会话相关的新闻
            deleted_news = 0
            for session_id in session_ids:
                news_result = await news_collection.delete_many({"session_id": session_id})
                deleted_news += news_result.deleted_count
                
                # 级联删除会话记忆
                try:
                    self.memory_store.clear_memory(session_id)
                    logger.info(f"删除会话记忆: {session_id}")
                except Exception as e:
                    logger.warning(f"删除会话记忆失败 {session_id}: {str(e)}")
            
            # 级联删除用户的所有会话
            sessions_result = await sessions_collection.delete_many({"user_id": user_id})
            deleted_sessions = sessions_result.deleted_count
            
            # 删除用户
            user_result = await users_collection.delete_one({"_id": user_object_id})
            
            if user_result.deleted_count > 0:
                logger.info(f"用户删除成功: {user['username']} (ID: {user_id})，级联删除 {deleted_sessions} 个会话，{deleted_news} 条新闻")
                return {
                    "status": "success",
                    "message": f"用户 {user['username']} 删除成功",
                    "deleted_sessions": deleted_sessions,
                    "deleted_news": deleted_news
                }
            else:
                return {
                    "status": "error",
                    "message": "删除用户失败",
                    "deleted_sessions": deleted_sessions,
                    "deleted_news": deleted_news
                }
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return {
                "status": "error",
                "message": f"删除失败: {str(e)}",
                "deleted_sessions": 0,
                "deleted_news": 0
            }
    
    async def create_session(self, request: UserSessionRequest) -> UserSessionResult:
        """
        创建用户会话
        
        Args:
            request: 会话创建请求
            
        Returns:
            UserSessionResult: 创建结果
        """
        logger.info(f"为用户 {request.user_id} 创建会话")
        
        try:
            db = await get_mongodb_database()
            if db is None:
                return UserSessionResult(
                    session_id="",
                    session_name=""
                )
            
            users_collection = db[Collections.USERS]
            sessions_collection = db[Collections.USER_SESSIONS]
            
            # 验证用户是否存在
            try:
                user_object_id = ObjectId(request.user_id)
                user = await users_collection.find_one({"_id": user_object_id})
            except Exception:
                return UserSessionResult(
                    session_id="",
                    session_name=""
                )
            
            if not user:
                return UserSessionResult(
                    session_id="",
                    session_name=""
                )
            
            # 生成会话名称
            session_name = request.session_name or str(uuid.uuid4())
            
            # 创建会话文档
            session_doc = {
                "user_id": request.user_id,
                "session_name": session_name
            }
            
            # 保存到数据库
            result = await sessions_collection.insert_one(session_doc)
            session_id = str(result.inserted_id)
            
            logger.info(f"会话创建成功: {session_name} (ID: {session_id})")
            
            return UserSessionResult(
                session_id=session_id,
                session_name=session_name
            )
            
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            return UserSessionResult(
                session_id="",
                session_name=""
            )
    
    async def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 会话列表和统计信息
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                return {"error": "数据库连接失败"}

            sessions_collection = db[Collections.USER_SESSIONS]
            
            # 会话表中的user_id存储为字符串，直接使用字符串查询
            sessions = []
            async for session in sessions_collection.find({"user_id": user_id}):
                sessions.append({
                    "session_id": str(session["_id"]),
                    "session_name": session["session_name"]
                })

            return {
                "user_id": user_id,
                "sessions": sessions,
                "session_count": len(sessions),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"获取用户会话失败: {str(e)}")
            return {"error": f"获取会话失败: {str(e)}"}
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除指定会话（级联删除相关新闻）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            db = await get_mongodb_database()
            if db is None:
                return {
                    "status": "error", 
                    "message": "数据库连接失败",
                    "deleted_news": 0
                }
            
            sessions_collection = db[Collections.USER_SESSIONS]
            news_collection = db[Collections.NEWS]
            
            # 检查会话是否存在
            try:
                session_object_id = ObjectId(session_id)
                session = await sessions_collection.find_one({"_id": session_object_id})
            except Exception:
                return {
                    "status": "error", 
                    "message": "会话ID格式错误",
                    "deleted_news": 0
                }
            
            if not session:
                return {
                    "status": "error", 
                    "message": "会话不存在",
                    "deleted_news": 0
                }
            
            # 级联删除会话相关的新闻
            news_result = await news_collection.delete_many({"session_id": session_id})
            deleted_news = news_result.deleted_count
            
            # 级联删除会话记忆
            try:
                self.memory_store.clear_memory(session_id)
                logger.info(f"删除会话记忆: {session_id}")
            except Exception as e:
                logger.warning(f"删除会话记忆失败: {str(e)}")
            
            # 删除会话
            session_result = await sessions_collection.delete_one({"_id": session_object_id})
            
            if session_result.deleted_count > 0:
                logger.info(f"会话删除成功: {session_id}，级联删除 {deleted_news} 条新闻")
                return {
                    "status": "success", 
                    "message": f"会话删除成功，级联删除 {deleted_news} 条新闻",
                    "deleted_news": deleted_news
                }
            else:
                return {
                    "status": "error", 
                    "message": "删除会话失败",
                    "deleted_news": deleted_news
                }
            
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            return {
                "status": "error", 
                "message": f"删除失败: {str(e)}",
                "deleted_news": 0
            }
    
    async def delete_user_by_credentials(self, username: str, password: str) -> Dict[str, Any]:
        """
        根据用户名和密码删除用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Dict: 删除结果
        """
        try:
            # 先验证用户身份
            login_request = UserLoginRequest(username=username, password=password)
            user_result = await self.login_user(login_request)
            
            if not user_result.user_id:
                return {
                    "status": "error",
                    "message": "用户名或密码错误",
                    "deleted_sessions": 0
                }
            
            # 验证成功后删除用户
            return await self.delete_user(user_result.user_id)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"删除失败: {str(e)}",
                "deleted_sessions": 0,
                "deleted_news": 0
            }
    
    def _hash_password(self, password: str) -> str:
        """生成密码哈希"""
        # 使用 PBKDF2 + SHA256 生成密码哈希
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{pwdhash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(':')
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return pwdhash.hex() == stored_hash
        except Exception:
            return False


# 全局服务实例（单例模式）
_user_auth_service: Optional[UserAuthService] = None


async def get_user_auth_service() -> UserAuthService:
    """获取用户认证服务实例（单例模式）"""
    global _user_auth_service
    if _user_auth_service is None:
        _user_auth_service = UserAuthService()
    return _user_auth_service
