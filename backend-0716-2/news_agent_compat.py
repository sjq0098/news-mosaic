"""
智能体工具调用兼容接口
保持与原始 smart_news_service.py 相同的公共接口，供智能体工具使用
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.news_service import get_news_service
from models.news import NewsSearchRequest, NewsSearchResult, NewsRefreshResult

logger = logging.getLogger(__name__)


async def smart_search_news(
    session_id: str,
    keywords: List[str],
    num_results: int = 10,
    language: str = "zh-cn",
    country: str = "cn",
    time_period: str = "1d"
) -> NewsSearchResult:
    """
    智能搜索新闻并入库（智能体工具调用接口）
    
    核心特性：
    - 智能去重：基于标题和URL字符串直接比较去重
    - 关键词丰富：相同新闻的关键词会自动合并
    - 结构化存储：统一的数据库结构
    - 自动清理：搜索前自动清理该会话的过期新闻
    
    Args:
        session_id: 会话ID
        keywords: 搜索关键词列表
        num_results: 搜索结果数量，默认10，最大50
        language: 搜索语言，默认zh-cn
        country: 搜索地区，默认cn
        time_period: 时间范围，默认1d（1天），可选1w（1周）、1m（1月）
        
    Returns:
        NewsSearchResult: 搜索和入库结果
    """
    try:
        # 参数验证和修正
        if not session_id:
            return NewsSearchResult(
                query="",
                total_found=0,
                saved_count=0,
                updated_count=0,
                search_time=0.0,
                timestamp=datetime.now(),
                news_ids=[],
                status="error",
                message="会话ID不能为空"
            )
            
        if not keywords:
            return NewsSearchResult(
                query="",
                total_found=0,
                saved_count=0,
                updated_count=0,
                search_time=0.0,
                timestamp=datetime.now(),
                news_ids=[],
                status="error",
                message="关键词列表不能为空"
            )
        
        # 限制搜索结果数量
        if num_results <= 0:
            num_results = 1
        elif num_results > 50:
            num_results = 50
            
        service = await get_news_service()
        request = NewsSearchRequest(
            session_id=session_id,
            keywords=keywords,
            num_results=num_results,
            language=language,
            country=country,
            time_period=time_period
        )
        return await service.search_and_save_news(request)
        
    except Exception as e:
        logger.error(f"智能体调用接口错误: {str(e)}")
        return NewsSearchResult(
            query=" ".join(keywords) if keywords else "",
            total_found=0,
            saved_count=0,
            updated_count=0,
            search_time=0.0,
            timestamp=datetime.now(),
            news_ids=[],
            status="error",
            message=f"调用失败: {str(e)}"
        )


async def refresh_news_database(session_id: str, expire_days: int = 3) -> NewsRefreshResult:
    """
    刷新指定会话的新闻数据库（智能体工具调用接口）
    
    刷新逻辑：
    1. 查找并删除指定会话超过指定天数的新闻
    2. 收集删除新闻的关键词
    3. 用这些关键词重新搜索最新新闻
    
    Args:
        session_id: 会话ID
        expire_days: 过期天数，默认3天
        
    Returns:
        NewsRefreshResult: 刷新结果
    """
    if not session_id:
        return NewsRefreshResult(
            cleaned_count=0,
            refreshed_keywords=[],
            new_articles_count=0,
            refresh_time=0.0,
            timestamp=datetime.now(),
            status="error",
            message="会话ID不能为空"
        )
        
    service = await get_news_service()
    return await service.refresh_expired_news(session_id, expire_days)


async def get_news_statistics(session_id: str = None) -> Dict[str, Any]:
    """
    获取新闻数据库统计信息（智能体工具调用接口）
    
    Args:
        session_id: 会话ID，如果提供则只统计该会话的新闻，否则统计所有新闻
    
    Returns:
        Dict: 包含总数、热门关键词、最新更新时间等统计信息
    """
    try:
        service = await get_news_service()
        stats = await service.get_news_statistics(session_id)
        
        # 转换为字典格式以保持兼容性
        if stats.status == "error":
            return {"error": "获取统计信息失败"}
        
        return {
            "session_id": stats.session_id,
            "total_count": stats.total_count,
            "today_count": stats.today_count,
            "latest_date": stats.latest_date,
            "top_keywords": stats.top_keywords,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"获取新闻统计失败: {str(e)}")
        return {"error": f"获取统计信息失败: {str(e)}"}


async def get_session_news_list(session_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    获取指定会话的新闻列表（智能体工具调用接口）
    
    Args:
        session_id: 会话ID
        limit: 返回数量限制，默认20
        offset: 偏移量，默认0
        
    Returns:
        Dict: 包含新闻列表和统计信息
    """
    try:
        service = await get_news_service()
        result = await service.get_session_news_list(session_id, limit, offset)
        
        # 转换为字典格式以保持兼容性
        if result.status == "error":
            return {"error": "获取新闻列表失败"}
        
        return {
            "session_id": result.session_id,
            "news_list": result.news_list,
            "total_count": result.total_count,
            "returned_count": result.returned_count,
            "offset": result.offset,
            "limit": result.limit,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"获取会话新闻列表失败: {str(e)}")
        return {"error": f"获取新闻列表失败: {str(e)}"}


# 向后兼容：保持原有函数名
async def get_smart_news_service():
    """获取智能新闻服务实例（向后兼容）"""
    return await get_news_service()


async def get_news_agent_service():
    """获取智能新闻助手服务实例"""
    from services.news_agent_service import get_news_agent_service as _get_agent_service
    return await _get_agent_service()


# 导出所有接口函数供智能体使用
__all__ = [
    "smart_search_news",
    "refresh_news_database", 
    "get_news_statistics",
    "get_session_news_list",
    "get_smart_news_service",
    "get_news_agent_service"
]
