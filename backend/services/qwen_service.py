"""
QWEN 模型服务 - 处理与通义千问 API 的交互
"""

import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import httpx
from loguru import logger

from core.config import settings
from models.chat import ChatMessage


@dataclass
class QWENResponse:
    """QWEN 响应数据类"""
    content: str
    tokens_used: int
    generation_time: float
    news_ids: List[str] = None
    
    def __post_init__(self):
        if self.news_ids is None:
            self.news_ids = []


class QWENService:
    """QWEN 模型服务"""
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.base_url = settings.QWEN_BASE_URL
        self.model = settings.QWEN_MODEL
        self.client = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self.client
    
    async def generate_response(
        self,
        user_message: str,
        chat_history: List[ChatMessage] = None,
        include_news: bool = True,
        news_limit: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> QWENResponse:
        """
        使用 QWEN 生成回复
        
        Args:
            user_message: 用户消息
            chat_history: 聊天历史
            include_news: 是否包含新闻搜索
            news_limit: 新闻数量限制
            temperature: 生成温度
            max_tokens: 最大令牌数
        """
        start_time = time.time()
        
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(include_news)
            
            # 构建消息历史
            messages = self._build_message_history(
                system_prompt, 
                user_message, 
                chat_history
            )
            
            # 如果需要新闻，先搜索相关新闻
            relevant_news = []
            if include_news:
                relevant_news = await self._search_relevant_news(
                    user_message, 
                    limit=news_limit
                )
                
                # 将新闻信息添加到消息中
                if relevant_news:
                    news_context = self._format_news_context(relevant_news)
                    messages.append({
                        "role": "system",
                        "content": f"相关新闻信息：\n{news_context}"
                    })
            
            # 调用 QWEN API
            response = await self._call_qwen_api(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            generation_time = time.time() - start_time
            
            return QWENResponse(
                content=response["content"],
                tokens_used=response["tokens_used"],
                generation_time=generation_time,
                news_ids=[news["id"] for news in relevant_news] if relevant_news else []
            )
            
        except Exception as e:
            logger.error(f"QWEN 生成回复失败: {e}")
            # 返回错误回复
            return QWENResponse(
                content="抱歉，我遇到了一些问题，无法生成回复。请稍后再试。",
                tokens_used=0,
                generation_time=time.time() - start_time,
                news_ids=[]
            )
    
    def _build_system_prompt(self, include_news: bool = True) -> str:
        """构建系统提示词"""
        base_prompt = """你是一个专业的新闻分析助手，名叫 News Mosaic AI。你的任务是：

1. 帮助用户理解和分析新闻内容
2. 提供客观、准确的信息摘要
3. 进行情感分析和观点提炼
4. 回答与新闻相关的问题

请遵循以下原则：
- 保持客观中立，不带个人偏见
- 提供准确、有用的信息
- 使用简洁明了的中文回复
- 当涉及敏感话题时保持谨慎
- 如果信息不确定，请明确说明"""

        if include_news:
            base_prompt += """

当用户询问新闻相关问题时，我会为你提供相关的新闻信息。请基于这些新闻内容来回答用户的问题，并在适当时候引用具体的新闻内容。"""

        return base_prompt
    
    def _build_message_history(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: List[ChatMessage] = None
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息（保留最近的几条）
        if chat_history:
            # 只保留最近的 8 条消息以控制上下文长度
            recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
            
            for msg in recent_history:
                if msg.role in ["user", "assistant"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _search_relevant_news(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索相关新闻"""
        try:
            # 这里应该调用新闻搜索服务
            # 暂时返回空列表，实际实现时需要集成新闻搜索
            from services.news_service import NewsService
            news_service = NewsService()
            
            # 模拟搜索结果
            return []
            
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            return []
    
    def _format_news_context(self, news_list: List[Dict[str, Any]]) -> str:
        """格式化新闻上下文"""
        if not news_list:
            return ""
        
        context_parts = []
        for i, news in enumerate(news_list, 1):
            part = f"{i}. 标题：{news.get('title', '未知')}\n"
            part += f"   摘要：{news.get('summary', '无摘要')}\n"
            part += f"   发布时间：{news.get('published_at', '未知')}\n"
            if news.get('sentiment_label'):
                part += f"   情感倾向：{news.get('sentiment_label')}\n"
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    async def _call_qwen_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """调用 QWEN API"""
        client = await self._get_client()
        
        # 构建请求参数
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 解析响应
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                content = choice["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                
                return {
                    "content": content,
                    "tokens_used": tokens_used
                }
            else:
                raise ValueError("API 响应格式异常")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"QWEN API HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"QWEN API 调用失败: {e}")
            raise
    
    async def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        try:
            client = await self._get_client()
            
            # 测试 API 连接
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            start_time = time.time()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=test_payload
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "model": self.model,
                    "response_time": response_time,
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "error",
                    "model": self.model,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.aclose()
            self.client = None 