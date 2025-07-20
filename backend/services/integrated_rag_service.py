"""
集成RAG服务 - 既生成新闻卡片又进行智能对话
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from loguru import logger

from services.qwen_service import QWENService
from services.embedding_service import QWenEmbeddingService
from services.rag_enhanced_card_service import RAGEnhancedCardService
from models.news import NewsModel
from models.news_card import NewsCardRequest, NewsCardResponse
from mock_data.news_samples import mock_news_db


class IntegratedRAGService:
    """集成RAG服务 - 新闻卡片生成 + 智能对话"""
    
    def __init__(self):
        self.qwen_service = QWENService()
        self.embedding_service = QWenEmbeddingService()
        self.card_service = RAGEnhancedCardService()
        
        # 模拟向量存储
        self.vector_store = {}
        self.news_embeddings = {}
        
        logger.info("集成RAG服务已初始化")
    
    async def initialize_pipeline(self):
        """初始化流水线 - 为所有新闻生成embedding"""
        logger.info("🚀 开始初始化集成RAG流水线...")
        
        all_news = mock_news_db.get_all_news()
        logger.info(f"📰 加载了 {len(all_news)} 条模拟新闻")
        
        for i, news_data in enumerate(all_news):
            await self._process_news_embedding(news_data)
            logger.info(f"✅ 处理新闻 {i+1}/{len(all_news)}: {news_data['title'][:50]}...")
        
        logger.info(f"🎯 集成RAG流水线初始化完成！共处理 {len(all_news)} 条新闻")
    
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
            
        except Exception as e:
            logger.error(f"为新闻 {news_id} 生成embedding失败: {e}")
    
    async def search_relevant_news(
        self, 
        query: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """基于查询检索相关新闻"""
        try:
            # 为查询生成embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # 计算相似度
            similarities = []
            
            for news_id, stored_data in self.news_embeddings.items():
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
        """生成新闻卡片（修复版本）"""
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
            
            # 创建请求
            request = NewsCardRequest(
                news_id=news_data["id"],
                include_sentiment=True,
                include_entities=True,
                include_summary=True
            )
            
            # 使用修复后的卡片服务生成卡片
            card_response = await self.card_service.generate_card_with_rag(news_model, request)
            logger.info(f"✅ 成功生成新闻卡片: {news_data['id']}")
            return card_response
            
        except Exception as e:
            logger.error(f"生成新闻卡片失败: {e}")
            return None
    
    async def chat_with_news_context(
        self, 
        user_query: str,
        max_context_news: int = 3
    ) -> Dict[str, Any]:
        """基于新闻上下文进行对话"""
        try:
            start_time = time.time()
            
            # 1. 检索相关新闻
            relevant_news = await self.search_relevant_news(user_query, top_k=max_context_news)
            
            if not relevant_news:
                logger.warning("未找到相关新闻，使用通用回复")
                return {
                    "user_query": user_query,
                    "ai_response": "抱歉，我没有找到与您问题相关的新闻信息。",
                    "relevant_news": [],
                    "news_card": None,
                    "processing_time": time.time() - start_time
                }
            
            # 2. 为最相关的新闻生成卡片
            top_news = relevant_news[0]["news_data"]
            news_card = await self.generate_news_card(top_news)
            
            # 3. 构建新闻上下文
            news_context = self._build_news_context(relevant_news)
            
            # 4. 构建完整提示
            full_prompt = self._build_chat_prompt(user_query, news_context)
            
            # 5. 调用QWEN生成回复
            response = await self.qwen_service.generate_response(
                user_message=full_prompt,
                chat_history=[],
                include_news=False,
                temperature=0.7,
                max_tokens=800
            )
            
            # 6. 组织返回结果
            result = {
                "user_query": user_query,
                "ai_response": response.content,
                "relevant_news": [
                    {
                        "title": news["news_data"]["title"],
                        "source": news["news_data"]["source"],
                        "similarity": news["similarity_score"],
                        "category": news["news_data"]["category"],
                        "url": news["news_data"]["url"]
                    }
                    for news in relevant_news
                ],
                "news_card": {
                    "card_id": news_card.card.metadata.card_id if news_card else None,
                    "summary": news_card.card.metadata.summary if news_card else None,
                    "importance_level": news_card.card.metadata.importance_level.value if news_card else None,
                    "sentiment_label": news_card.card.metadata.sentiment_label.value if news_card else None,
                    "generation_time": news_card.processing_time if news_card else None
                } if news_card else None,
                "tokens_used": response.tokens_used,
                "generation_time": response.generation_time,
                "processing_time": time.time() - start_time
            }
            
            logger.info(f"💬 完整对话流程完成，耗时: {result['processing_time']:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"基于新闻上下文对话失败: {e}")
            return {
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _build_news_context(self, relevant_news: List[Dict[str, Any]]) -> str:
        """构建新闻上下文"""
        context_parts = []
        
        for i, news_item in enumerate(relevant_news, 1):
            news = news_item["news_data"]
            similarity = news_item["similarity_score"]
            
            context_part = f"""
新闻 {i} (相似度: {similarity:.3f}):
标题: {news['title']}
来源: {news['source']}
分类: {news['category']}
内容摘要: {news['content'][:400]}...
发布时间: {news['published_at'].strftime('%Y-%m-%d %H:%M')}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _build_chat_prompt(self, user_query: str, news_context: str) -> str:
        """构建对话提示"""
        return f"""
你是一个专业的新闻分析助手。请根据提供的相关新闻信息，回答用户的问题。

相关新闻信息:
{news_context}

用户问题: {user_query}

请提供专业、准确的分析回复。回复应该:
1. 基于提供的新闻信息
2. 结构清晰，逻辑严谨
3. 客观中性，避免主观推测
4. 如果涉及多条新闻，可以进行对比分析

回复:
"""

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """获取流水线状态"""
        return {
            "total_news": len(self.news_embeddings),
            "service_status": "ready",
            "categories": list(set([
                news_data["news_data"]["category"] 
                for news_data in self.news_embeddings.values()
            ])),
            "features": [
                "新闻向量检索",
                "结构化卡片生成", 
                "智能对话回复",
                "数据格式映射",
                "并发处理支持"
            ]
        }


# 创建全局实例
integrated_rag = IntegratedRAGService() 