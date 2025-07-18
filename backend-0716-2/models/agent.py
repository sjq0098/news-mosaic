"""
智能体模型定义
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
try:
    # 尝试新版本的导入
    from langgraph.graph.message import add_messages
except ImportError:
    # 降级到兼容版本
    def add_messages(left: list, right: list) -> list:
        """消息列表合并函数（兼容版本）"""
        return left + right

from models.user import UserPreferences


class AgentState(TypedDict):
    """智能体状态定义"""
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    user_preferences: Optional[UserPreferences]
    extracted_keywords: List[str]
    search_result: Optional[Dict[str, Any]]
    response_type: str  # intro, refuse, news_general, news_specific, manage_interests
    interest_operation: Optional[str]  # add, remove, list - 兴趣管理操作类型
    interests_to_manage: List[str]  # 要管理的兴趣关键词
