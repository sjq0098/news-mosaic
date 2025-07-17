"""
智能体模型定义
"""

from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph.message import add_messages
from models.user import UserPreferences


class AgentState(TypedDict):
    """智能体状态定义，消息自动合并，字段清晰对应工作流逻辑"""
    messages: List  # 使用 langgraph 消息合并机制，动态合并新消息
    user_id: str
    session_id: str
    user_preferences: Optional[UserPreferences]  # 用户偏好数据，兴趣相关
    extracted_keywords: List[str]                # 关键词抽取结果
    search_result: Optional[Dict[str, Any]]      # 搜索结果
    response_type: str                            # 响应类型，如 intro, refuse, news_general 等
    interest_operation: Optional[str]             # 兴趣操作类型，add/remove/list 等
    interests_to_manage: List[str]                # 待管理兴趣关键词列表
