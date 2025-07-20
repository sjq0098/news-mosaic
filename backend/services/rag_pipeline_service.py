"""
RAG流水线服务 - 完整的向量检索与LLM调度流程
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from loguru import logger
import json

from services.qwen_service import QWENService
from services.embedding_service import QWenEmbeddingService
from services.news_chat_service import NewsChatService
from services.rag_enhanced_card_service import RAGEnhancedCardService
from models.news import NewsModel
from models.news_card import NewsCardRequest, NewsCardResponse
from mock_data.news_samples import mock_news_db


class RAGPipelineService:
    """RAG流水线服务 - 从新闻数据到智能回复的完整流程"""
    
    def __init__(self):
        self.qwen_service = QWENService()
        self.embedding_service = QWenEmbeddingService()
        self.chat_service = NewsChatService()
        self.card_service = RAGEnhancedCardService()
        
        # 模拟向量存储（实际应用中应该是Pinecone/Weaviate）
        self.vector_store = {}
        self.news_embeddings = {}
        
        logger.info("RAG流水线服务已初始化")
    
    async def initialize_pipeline(self):
        """初始化流水线 - 为所有新闻生成embedding"""
        logger.info("🚀 开始初始化RAG流水线...")
        
        # 获取所有模拟新闻数据
        all_news = mock_news_db.get_all_news()
        logger.info(f"📰 加载了 {len(all_news)} 条模拟新闻")
        
        # 为每条新闻生成embedding
        for i, news_data in enumerate(all_news):
            await self._process_news_embedding(news_data)
            logger.info(f"✅ 处理新闻 {i+1}/{len(all_news)}: {news_data['title'][:50]}...")
        
        logger.info(f"🎯 RAG流水线初始化完成！共处理 {len(all_news)} 条新闻")
    
    async def _process_news_embedding(self, news_data: Dict[str, Any]):
        """为单条新闻生成embedding"""
        news_id = news_data["id"]
        
        # 组合文本：标题 + 内容摘要
        combined_text = f"{news_data['title']}\n\n{news_data['content'][:500]}..."
        
        try:
            # 生成embedding
            embedding = await self.embedding_service.generate_embedding(combined_text)
            
            # 存储embedding和元数据
            self.news_embeddings[news_id] = {
                "embedding": embedding,
                "text": combined_text,
                "news_data": news_data
            }
            
            # 模拟向量存储（实际应用中会存储到向量数据库）
            self.vector_store[news_id] = {
                "vector": embedding,
                "metadata": {
                    "title": news_data["title"],
                    "category": news_data["category"],
                    "published_at": news_data["published_at"].isoformat(),
                    "source": news_data["source"],
                    "tags": news_data["tags"]
                }
            }
            
        except Exception as e:
            logger.error(f"为新闻 {news_id} 生成embedding失败: {e}")
    
    async def search_relevant_news(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """基于查询检索相关新闻"""
        try:
            # 为查询生成embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # 计算相似度（简化版本，实际应该使用向量数据库的相似度搜索）
            similarities = []
            
            for news_id, stored_data in self.news_embeddings.items():
                # 简单的cosine相似度计算
                similarity = self._cosine_similarity(
                    query_embedding, 
                    stored_data["embedding"]
                )
                
                similarities.append({
                    "news_id": news_id,
                    "similarity": similarity,
                    "news_data": stored_data["news_data"]
                })
            
            # 按相似度排序并返回top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            relevant_news = []
            for item in similarities[:top_k]:
                relevant_news.append({
                    "news_data": item["news_data"],
                    "similarity_score": item["similarity"]
                })
            
            logger.info(f"🔍 检索到 {len(relevant_news)} 条相关新闻")
            return relevant_news
            
        except Exception as e:
            logger.error(f"检索相关新闻失败: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            import numpy as np
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            return dot_product / (norm_vec1 * norm_vec2)
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0
    
    async def generate_news_card(self, news_data: Dict[str, Any]) -> Optional[NewsCardResponse]:
        """为新闻生成结构化卡片"""
        try:
            # 转换为NewsModel格式
            from models.news import NewsSource
            news_model = NewsModel(
                id=news_data["id"],
                title=news_data["title"],
                content=news_data["content"],
                source=NewsSource.MANUAL,  # 使用MANUAL作为默认来源
                url=news_data["url"],
                published_at=news_data["published_at"]
            )
            
            # 创建请求（添加必需的news_id字段）
            request = NewsCardRequest(
                news_id=news_data["id"],
                include_sentiment=True,
                include_entities=True,
                include_summary=True
            )
            
            # 生成卡片
            card_response = await self.card_service.generate_card_with_rag(news_model, request)
            return card_response
            
        except Exception as e:
            logger.error(f"生成新闻卡片失败: {e}")
            return None
    
    async def chat_with_news_context(
        self, 
        user_query: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """基于新闻上下文进行对话"""
        try:
            start_time = time.time()
            
            # 1. 检索相关新闻
            relevant_news = await self.search_relevant_news(user_query, top_k=3)
            
            if not relevant_news:
                logger.warning("未找到相关新闻，使用通用回复")
                return {
                    "response": "抱歉，我没有找到与您问题相关的新闻信息。",
                    "relevant_news": [],
                    "processing_time": time.time() - start_time
                }
            
            # 2. 如果没有会话，创建新会话
            if not session_id:
                # 使用第一条相关新闻创建会话
                first_news = relevant_news[0]["news_data"]
                from models.news import NewsSource
                news_model = NewsModel(
                    id=first_news["id"],
                    title=first_news["title"],
                    content=first_news["content"],
                    source=NewsSource.MANUAL,  # 使用MANUAL作为默认来源
                    url=first_news["url"],
                    published_at=first_news["published_at"]
                )
                
                # 创建新会话
                session = await self.chat_service.create_news_session(
                    user_id="demo_user", 
                    initial_news=news_model,
                    session_title=f"关于：{news_model.title[:30]}..."
                )
                session_id = session.id
                logger.info(f"🆕 创建新对话会话: {session_id}")
            
            # 3. 发送消息并获取回复
            chat_result = await self.chat_service.send_news_message(
                session_id, 
                user_query,
                user_id="demo_user"
            )
            
            # 4. 组织返回结果
            result = {
                "session_id": session_id,
                "user_query": user_query,
                "ai_response": chat_result["assistant_message"]["content"],
                "relevant_news": [
                    {
                        "title": news["news_data"]["title"],
                        "source": news["news_data"]["source"],
                        "similarity": news["similarity_score"],
                        "url": news["news_data"]["url"]
                    }
                    for news in relevant_news
                ],
                "suggested_questions": chat_result.get("suggested_questions", []),
                "processing_time": time.time() - start_time
            }
            
            logger.info(f"💬 对话完成，耗时: {result['processing_time']:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"基于新闻上下文对话失败: {e}")
            return {
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """获取流水线状态"""
        return {
            "total_news": len(self.news_embeddings),
            "vector_store_size": len(self.vector_store),
            "services_status": {
                "qwen_service": "ready",
                "embedding_service": "ready", 
                "chat_service": "ready",
                "card_service": "ready"
            },
            "categories": list(set([
                news_data["news_data"]["category"] 
                for news_data in self.news_embeddings.values()
            ]))
        }
    
    async def demo_complete_pipeline(self, query: str) -> Dict[str, Any]:
        """演示完整流水线的端到端过程"""
        logger.info(f"🎯 开始演示完整RAG流水线: {query}")
        
        pipeline_start = time.time()
        result = {
            "query": query,
            "steps": [],
            "final_result": None,
            "total_time": 0
        }
        
        try:
            # 步骤1: 检索相关新闻
            step1_start = time.time()
            relevant_news = await self.search_relevant_news(query, top_k=3)
            step1_time = time.time() - step1_start
            
            result["steps"].append({
                "step": "1. 新闻检索",
                "description": f"基于查询检索到 {len(relevant_news)} 条相关新闻",
                "time": step1_time,
                "data": [news["news_data"]["title"] for news in relevant_news[:3]]
            })
            
            if not relevant_news:
                result["final_result"] = "未找到相关新闻"
                return result
            
            # 步骤2: 生成新闻卡片
            step2_start = time.time()
            top_news = relevant_news[0]["news_data"]
            card_result = await self.generate_news_card(top_news)
            step2_time = time.time() - step2_start
            
            result["steps"].append({
                "step": "2. 新闻卡片生成",
                "description": "为最相关的新闻生成结构化卡片",
                "time": step2_time,
                "data": {
                    "title": card_result.news_id if card_result else "生成失败",
                    "status": "成功" if card_result else "失败"
                }
            })
            
            # 步骤3: 基于上下文对话
            step3_start = time.time()
            chat_result = await self.chat_with_news_context(query)
            step3_time = time.time() - step3_start
            
            result["steps"].append({
                "step": "3. 智能对话生成",
                "description": "基于新闻上下文生成AI回复",
                "time": step3_time,
                "data": {
                    "response_length": len(chat_result.get("ai_response", "")),
                    "has_suggestions": len(chat_result.get("suggested_questions", [])) > 0
                }
            })
            
            # 最终结果
            result["final_result"] = {
                "ai_response": chat_result.get("ai_response", ""),
                "relevant_news_count": len(relevant_news),
                "session_id": chat_result.get("session_id"),
                "suggested_questions": chat_result.get("suggested_questions", [])
            }
            
            result["total_time"] = time.time() - pipeline_start
            
            logger.info(f"✅ 完整流水线演示完成，总耗时: {result['total_time']:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"流水线演示失败: {e}")
            result["error"] = str(e)
            result["total_time"] = time.time() - pipeline_start
            return result


# 创建全局实例
rag_pipeline = RAGPipelineService() 