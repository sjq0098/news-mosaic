"""FAISS 本地向量数据库实现（仅用于开发/测试）"""

from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from .base import IVectorDB
from models.embedding import EmbeddingResult
from services.embedding_service import embedding_service


class FaissVectorDB(IVectorDB):
    """使用 LangChain-FAISS 在内存中保存向量，适合本地单进程测试。"""

    def __init__(self):
        # 使用同一 embedding_model，保证向量空间一致
        self._embedding_model = embedding_service.embedding_model
        self._vectorstore: FAISS | None = None

    # -------------------------------------------------
    # 接口实现
    # -------------------------------------------------
    def init_index(self, dimension: int) -> None:
        """FAISS 会在第一次 upsert 时自动创建索引，这里无需额外操作。"""
        if self._vectorstore is None:
            # 创建一个空向量库
            self._vectorstore = FAISS.from_texts([], self._embedding_model)

    def upsert_embeddings(self, results: List[EmbeddingResult]) -> None:
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        for r in results:
            texts.append(r.chunk.content)
            metadatas.append({
                "news_id": r.model_info.get("source_id"),
                "chunk_index": r.chunk.chunk_index,
                "title": r.chunk.metadata.get("title"),
                "published_at": r.chunk.metadata.get("published_at"),
            })

        if self._vectorstore is None:
            # 首次写入，用当前批次直接创建索引
            self._vectorstore = FAISS.from_texts(texts=texts, embedding=self._embedding_model, metadatas=metadatas)
        else:
            self._vectorstore.add_texts(texts=texts, metadatas=metadatas)

    def query_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self._vectorstore is None:
            return []
        docs_and_scores = self._vectorstore.similarity_search_with_score(query_text, k=top_k)
        results: List[Dict[str, Any]] = []
        for doc, score in docs_and_scores:
            results.append({
                "news_id": doc.metadata.get("news_id"),
                "score": score,
                "metadata": doc.metadata,
                "content": doc.page_content,
            })
        return results

    def delete_by_source(self, source_id: str) -> None:
        if self._vectorstore is None:
            return
        # FAISS 不提供按 metadata 删除，简单重建过滤
        all_docs: List[Document] = self._vectorstore.similarity_search("", k=10000)
        texts, metas = [], []
        for doc in all_docs:
            if doc.metadata.get("news_id") != source_id:
                texts.append(doc.page_content)
                metas.append(doc.metadata)
        # 重新构建索引
        self._vectorstore = FAISS.from_texts(texts=texts, metadatas=metas, embedding=self._embedding_model) 