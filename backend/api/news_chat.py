"""
新闻对话API - 提供智能新闻对话功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

from models.news import NewsModel
from models.chat import ChatSession, ChatMessage, MessageRole, MessageType
from services.news_chat_service import NewsChatService
from core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news-chat", tags=["新闻对话"])

# 请求/响应模型
class CreateChatSessionRequest(BaseModel):
    """创建对话会话请求"""
    session_title: Optional[str] = Field(None, description="会话标题")
    initial_news: Optional[NewsModel] = Field(None, description="初始新闻")

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    news_data: Optional[NewsModel] = Field(None, description="新闻数据（可选）")

class ChatResponse(BaseModel):
    """对话响应"""
    user_message: Dict[str, Any]
    assistant_message: Dict[str, Any]
    conversation_context: Dict[str, Any]
    suggested_questions: List[str] = Field(default_factory=list)

class SessionHistoryResponse(BaseModel):
    """会话历史响应"""
    session: Dict[str, Any]
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]

# 全局服务实例
chat_service = NewsChatService()

@router.post("/sessions", response_model=Dict[str, Any])
async def create_chat_session(
    request: CreateChatSessionRequest,
    current_user: str = Depends(get_current_user)
):
    """
    创建新闻对话会话
    
    可以选择性地提供初始新闻进行分析
    """
    try:
        session = await chat_service.create_news_session(
            user_id=current_user,
            initial_news=request.initial_news,
            session_title=request.session_title
        )
        
        # 如果有初始新闻，获取初始分析消息
        if request.initial_news:
            messages = chat_service._messages.get(session.id, [])
            return {
                "session": session.model_dump(),
                "initial_analysis": messages[-1].model_dump() if messages else None,
                "message": "会话创建成功，已完成初始新闻分析"
            }
        
        return {
            "session": session.model_dump(),
            "message": "会话创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建对话会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: str = Depends(get_current_user)
):
    """
    发送消息并获取AI回复
    
    支持：
    - 普通对话
    - 新闻分析请求
    - 追问和深度讨论
    """
    try:
        response = await chat_service.send_news_message(
            session_id=session_id,
            user_message=request.message,
            news_data=request.news_data,
            user_id=current_user
        )
        
        return ChatResponse(**response)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取会话历史记录
    """
    try:
        history = await chat_service.get_session_history(session_id)
        
        if "error" in history:
            raise HTTPException(status_code=404, detail=history["error"])
        
        return SessionHistoryResponse(**history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@router.get("/sessions/{session_id}/context")
async def get_conversation_context(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取对话上下文信息
    """
    try:
        context = chat_service._get_context_summary(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话上下文失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取上下文失败: {str(e)}")

@router.post("/sessions/{session_id}/analyze-news")
async def analyze_news_in_session(
    session_id: str,
    news: NewsModel,
    current_user: str = Depends(get_current_user)
):
    """
    在现有会话中分析新的新闻
    """
    try:
        response = await chat_service.send_news_message(
            session_id=session_id,
            user_message="请分析这条新闻",
            news_data=news,
            user_id=current_user
        )
        
        return {
            "analysis": response["assistant_message"],
            "suggested_questions": response["suggested_questions"],
            "context": response["conversation_context"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"分析新闻失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/sessions/{session_id}/suggestions")
async def get_conversation_suggestions(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取对话建议问题
    """
    try:
        if session_id not in chat_service._contexts:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        context = chat_service._contexts[session_id]
        
        if not context.news_cards:
            return {"suggestions": ["请先提供一条新闻进行分析"]}
        
        latest_card = context.news_cards[-1]
        suggestions = await chat_service._generate_suggested_questions(latest_card)
        
        return {
            "suggestions": suggestions,
            "news_title": latest_card.title,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取建议问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")

# 快速对话接口 - 无需创建会话
@router.post("/quick-chat")
async def quick_news_chat(
    news: NewsModel,
    message: str = Field(..., description="用户问题"),
    current_user: str = Depends(get_current_user)
):
    """
    快速新闻对话 - 无需创建会话
    
    适用于单次查询场景
    """
    try:
        # 创建临时会话
        session = await chat_service.create_news_session(
            user_id=current_user,
            initial_news=news,
            session_title="快速分析"
        )
        
        # 发送用户消息
        response = await chat_service.send_news_message(
            session_id=session.id,
            user_message=message,
            user_id=current_user
        )
        
        return {
            "analysis": response["assistant_message"],
            "suggested_questions": response["suggested_questions"],
            "news_card": response["assistant_message"]["metadata"].get("news_card"),
            "quick_session": True
        }
        
    except Exception as e:
        logger.error(f"快速对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

# 批量新闻对话
@router.post("/batch-analyze")
async def batch_news_analysis(
    news_list: List[NewsModel],
    analysis_type: str = Field("overview", description="分析类型: overview, comparison, trend"),
    current_user: str = Depends(get_current_user)
):
    """
    批量新闻分析对话
    """
    try:
        if len(news_list) > 10:
            raise HTTPException(status_code=400, detail="批量分析最多支持10条新闻")
        
        # 创建会话
        session = await chat_service.create_news_session(
            user_id=current_user,
            session_title=f"批量分析 - {len(news_list)}条新闻"
        )
        
        results = []
        
        # 分析每条新闻
        for i, news in enumerate(news_list):
            if analysis_type == "comparison" and i > 0:
                message = f"请与前一条新闻对比分析"
            elif analysis_type == "trend":
                message = f"请分析发展趋势"
            else:
                message = f"请分析这条新闻"
            
            response = await chat_service.send_news_message(
                session_id=session.id,
                user_message=message,
                news_data=news,
                user_id=current_user
            )
            
            results.append({
                "news_title": news.title,
                "analysis": response["assistant_message"]["content"],
                "analysis_type": analysis_type
            })
        
        # 生成总结
        if analysis_type == "comparison" and len(news_list) > 1:
            summary_response = await chat_service.send_news_message(
                session_id=session.id,
                user_message="请对以上所有新闻进行综合对比总结",
                user_id=current_user
            )
            
            results.append({
                "news_title": "综合总结",
                "analysis": summary_response["assistant_message"]["content"],
                "analysis_type": "summary"
            })
        
        return {
            "session_id": session.id,
            "analysis_results": results,
            "total_analyzed": len(news_list),
            "analysis_type": analysis_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "news_chat_api",
        "timestamp": datetime.utcnow()
    }