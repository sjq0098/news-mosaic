"""backend/services/vector_db/pinecone_db.py
Pinecone 向量数据库实现。
"""
from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from loguru import logger

try:
    import pinecone  # type: ignore
except ImportError:  # pragma: no cover
    pinecone = None  # type: ignore

from core.config import settings
from .base import IVectorDB, ScoredDocument


class PineconeVectorDB(IVectorDB):
    """基于 pinecone-client 的向量库封装"""

    def __init__(self):
        if pinecone is None:
            raise ImportError("请先 pip install pinecone-client")
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dim = settings.EMBEDDING_DIMENSION
        self._index = None

        pinecone.init(api_key=self.api_key, environment=self.environment)

    # ------------------------------------------------------------------
    def init_index(self) -> None:
        if self.index_name not in pinecone.list_indexes():
            logger.info(f"创建 Pinecone 索引: {self.index_name}")
            pinecone.create_index(name=self.index_name, dimension=self.dim, metric="cosine")
        self._index = pinecone.Index(self.index_name)

    # ------------------------------------------------------------------
    async def upsert_embeddings(
        self,
        embeddings: List[np.ndarray],
        ids: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if self._index is None:
            self.init_index()
        vectors = [(id_, vec.tolist(), meta) for id_, vec, meta in zip(ids, embeddings, metadatas)]
        self._index.upsert(vectors)

    # ------------------------------------------------------------------
    async def query(self, query_vector: np.ndarray, top_k: int = 5, **kwargs):
        if self._index is None:
            self.init_index()
        res = self._index.query(vector=query_vector.tolist(), top_k=top_k, include_metadata=True)
        docs: List[ScoredDocument] = []
        for match in res["matches"]:
            docs.append(
                ScoredDocument(
                    news_id=match["id"],
                    score=match["score"],
                    metadata=match.get("metadata", {}),
                )
            )
        return docs

    # ------------------------------------------------------------------
    async def delete(self, ids: List[str]):
        if self._index is None:
            self.init_index()
        self._index.delete(ids) 