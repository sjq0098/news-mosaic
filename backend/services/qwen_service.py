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
        # 强制使用正确的URL
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = settings.QWEN_MODEL
        self.client = None
        self.demo_mode = not settings.is_api_configured("qwen")
        
        if self.demo_mode:
            logger.warning("QWEN服务启用演示模式 - API未配置")
        else:
            logger.info(f"QWEN服务已初始化: {self.base_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0
            )
        
        return self.client
    
    async def _generate_demo_response(
        self, 
        user_message: str, 
        chat_history: List[ChatMessage] = None
    ) -> str:
        """生成演示模式回复"""
        prompt = user_message.lower()
        
        if "技术" in prompt or "突破" in prompt or "创新" in prompt:
            return """从技术分析角度看，这一突破具有重要意义：

**技术创新点**：
- 突破了传统方法的局限
- 在关键指标上有显著提升
- 为行业发展提供新思路

**影响分析**：
- 短期内将推动相关技术发展
- 可能催生新的应用场景
- 对产业链上下游产生积极影响

**发展建议**：
- 持续关注技术演进
- 评估对现有业务的影响
- 考虑相关投资机会

这是基于演示模式生成的回复，实际使用需要配置QWEN API。"""
        
        elif "对比" in prompt or "比较" in prompt:
            return """从对比分析角度看：

**优势方面**：
- 在某些指标上表现突出
- 具备独特的技术特点
- 市场定位相对明确

**差异化特征**：
- 与现有方案有所不同
- 针对特定场景优化
- 成本效益有所改善

这是演示模式下的对比分析，具体数据需要实际API支持。"""
        
        elif "预测" in prompt or "未来" in prompt:
            return """从未来发展趋势预测：

**短期前景**（1-2年）：
- 技术逐步成熟和完善
- 早期应用场景落地
- 行业标准逐步建立

**中长期展望**（3-5年）：
- 大规模商业化应用
- 形成完整产业生态
- 推动相关领域变革

这是演示模式的趋势预测，实际分析需要真实数据支持。"""
        
        else:
            return f"""感谢您的问题："{user_message}"

这是QWEN演示模式的回复。在演示模式下：
- 可以展示对话交互流程
- 提供模拟的智能回复
- 验证系统功能完整性

要获得真正的AI智能回复，请：
1. 配置正确的阿里云百炼API Key
2. 确保网络连接正常
3. 验证API额度充足

演示模式生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"""
    
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
        
        # 如果是演示模式，使用模拟回复
        if self.demo_mode:
            await asyncio.sleep(0.5)  # 模拟API延迟
            demo_content = await self._generate_demo_response(user_message, chat_history)
            return QWENResponse(
                content=demo_content,
                tokens_used=len(demo_content) // 4,  # 估算token数
                generation_time=time.time() - start_time,
                news_ids=[]
            )
        
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(include_news)
            
            # 构建消息历史
            messages = self._build_message_history(
                system_prompt, 
                user_message, 
                chat_history
            )
            
            # 如果需要新闻上下文，先获取相关新闻
            if include_news:
                news_context = await self._get_news_context(user_message, news_limit)
                if news_context:
                    # 在系统提示词中加入新闻上下文
                    enhanced_prompt = f"{system_prompt}\n\n相关新闻信息：\n{news_context}"
                    messages[0]["content"] = enhanced_prompt
            
            # 调用API
            api_response = await self._call_qwen_api(
                messages, 
                temperature, 
                max_tokens
            )
            
            return QWENResponse(
                content=api_response["content"],
                tokens_used=api_response["tokens_used"],
                generation_time=time.time() - start_time,
                news_ids=api_response.get("news_ids", [])
            )
            
        except Exception as e:
            logger.error(f"QWEN 生成回复失败: {e}")
            return QWENResponse(
                content="抱歉，我遇到了一些问题，无法生成回复。请稍后再试。",
                tokens_used=0,
                generation_time=time.time() - start_time,
                news_ids=[]
            )
    
    def _build_system_prompt(self, include_news: bool = True) -> str:
        """构建系统提示词"""
        base_prompt = """你是一个专业的新闻分析助手，具备以下能力：

1. 深度分析新闻事件的背景、影响和趋势
2. 提供客观、准确的信息解读
3. 回答用户关于新闻的各种问题
4. 保持中立立场，避免主观偏见

请用中文回复，语言简洁明了，逻辑清晰。"""
        
        if include_news:
            base_prompt += "\n\n如果有相关新闻信息，请结合这些信息进行分析和回答。"
        
        return base_prompt
    
    def _build_message_history(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: List[ChatMessage] = None
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话
        if chat_history:
            for msg in chat_history[-10:]:  # 只保留最近10条
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _get_news_context(self, query: str, limit: int = 5) -> str:
        """获取相关新闻上下文"""
        # TODO: 实现新闻检索逻辑
        # 这里应该调用向量数据库或搜索服务
        return ""
    
    def _format_news_context(self, news_list: List[Dict]) -> str:
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


# 创建全局实例
qwen_service = QWENService()


async def get_qwen_service() -> QWENService:
    """获取 QWEN 服务实例"""
    return qwen_service 