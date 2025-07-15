"""
QWen Embedding 生成服务
"""

import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

# LangChain 组件
from langchain.text_splitter import RecursiveCharacterTextSplitter
# 使用通义 DashScope Embedding
from langchain_community.embeddings.dashscope import DashScopeEmbeddings

from core.config import settings
from models.embedding import TextChunk, EmbeddingResult, EmbeddingResultModel


class QWenEmbeddingService:
    """QWen Embedding 服务"""
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.base_url = settings.QWEN_BASE_URL
        self.model_name = "text-embedding-v3"

        # 使用 LangChain 的递归式分块器（与原逻辑保持 chunk_size/overlap 一致）
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=512,
            chunk_overlap=100,
            encoding_name="cl100k_base"
        )

        # DashScopeEmbeddings 直接调用通义向量接口，无需手动拼接 URL
        self.embedding_model = DashScopeEmbeddings(
            model=self.model_name,
            dashscope_api_key=self.api_key,
        )

        self.batch_size = 10  # 批量处理大小
    
    async def chunk_text(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        文本分块
        
        Args:
            text: 待分块的文本
            metadata: 元数据
            
        Returns:
            文本分块列表
        """
        try:
            start_time = time.time()
            # 使用 LangChain splitter
            docs = self.text_splitter.create_documents([text], metadatas=[metadata or {}])

            # 转换为内部 TextChunk 结构
            chunks = []
            for i, doc in enumerate(docs):
                # 这里无法直接获取字符位置，简单使用递增索引
                chunks.append(TextChunk(
                    content=doc.page_content,
                    chunk_index=i,
                    token_count=self.text_splitter._length_function(doc.page_content),
                    start_pos=-1,
                    end_pos=-1,
                    metadata=doc.metadata
                ))
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"文本分块完成: {len(chunks)} 个分块, "
                f"耗时: {processing_time:.2f}s"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"文本分块失败: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        生成单个文本的 embedding
        
        Args:
            text: 文本内容
            
        Returns:
            embedding 向量
        """
        # 使用 LangChain 同步接口，在异步环境下借助 asyncio.to_thread
        vector = await asyncio.to_thread(self.embedding_model.embed_query, text)
        return np.array(vector, dtype=np.float32)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量生成 embeddings
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding 向量列表
        """
        # LangChain embed_documents 是同步函数，同样使用线程池异步化
        vectors = await asyncio.to_thread(self.embedding_model.embed_documents, texts)
        return [np.array(v, dtype=np.float32) for v in vectors]
    
    async def process_text(
        self,
        text: str,
        source_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[EmbeddingResult]:
        """
        完整处理文本：分块 + 生成 embeddings
        
        Args:
            text: 待处理的文本
            source_id: 来源 ID
            metadata: 元数据
            
        Returns:
            处理结果列表
        """
        try:
            start_time = time.time()
            
            # 1. 文本分块
            chunks = await self.chunk_text(text, metadata)
            
            if not chunks:
                logger.warning("文本分块结果为空")
                return []
            
            # 2. 批量生成 embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            results = []
            
            # 分批处理
            for i in range(0, len(chunk_texts), self.batch_size):
                batch_texts = chunk_texts[i:i + self.batch_size]
                batch_chunks = chunks[i:i + self.batch_size]
                
                batch_start_time = time.time()
                embeddings = await self.generate_embeddings_batch(batch_texts)
                batch_processing_time = time.time() - batch_start_time
                
                # 创建结果对象
                for chunk, embedding in zip(batch_chunks, embeddings):
                    result = EmbeddingResult(
                        chunk=chunk,
                        embedding=embedding,
                        model_info={
                            "model": self.model_name,
                            "version": "v3",
                            "dimension": len(embedding),
                            "source_id": source_id
                        },
                        processing_time=batch_processing_time / len(batch_texts)
                    )
                    results.append(result)
                
                logger.info(
                    f"批次 {i//self.batch_size + 1} 处理完成: "
                    f"{len(batch_texts)} 个分块, 耗时: {batch_processing_time:.2f}s"
                )
            
            total_processing_time = time.time() - start_time
            logger.info(
                f"文本处理完成: {len(results)} 个分块, "
                f"总耗时: {total_processing_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"文本处理失败: {e}")
            raise
    
    async def process_texts_batch(
        self,
        texts: List[str],
        source_ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[List[EmbeddingResult]]:
        """
        批量处理多个文本
        
        Args:
            texts: 文本列表
            source_ids: 来源 ID 列表
            metadatas: 元数据列表
            
        Returns:
            每个文本的处理结果列表
        """
        if len(texts) != len(source_ids):
            raise ValueError("文本数量和来源 ID 数量不匹配")
        
        if metadatas and len(metadatas) != len(texts):
            raise ValueError("元数据数量和文本数量不匹配")
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # 并发处理所有文本
        tasks = [
            self.process_text(text, source_id, metadata)
            for text, source_id, metadata in zip(texts, source_ids, metadatas)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"文本 {source_ids[i]} 处理失败: {result}")
                final_results.append([])
            else:
                final_results.append(result)
        
        return final_results
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        # 兼容新版 LangChain，属性可能改为 _chunk_size/_chunk_overlap
        chunk_size = getattr(self.text_splitter, "chunk_size", getattr(self.text_splitter, "_chunk_size", None))
        chunk_overlap = getattr(self.text_splitter, "chunk_overlap", getattr(self.text_splitter, "_chunk_overlap", None))

        return {
            "model_name": self.model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "batch_size": self.batch_size,
            "api_endpoint": self.base_url
        }
    
    async def close(self):
        """关闭客户端"""
        pass


# 创建全局服务实例
embedding_service = QWenEmbeddingService()