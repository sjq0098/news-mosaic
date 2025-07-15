"""In-memory vector DB 实现，仅用于单机测试，不持久化。"""
from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from numpy.linalg import norm

from .base import IVectorDB, ScoredDocument


class MemoryVectorDB(IVectorDB):
    """简单的内存向量数据库，全部数据存在 Python dict 中。"""

    def __init__(self, dim: int):
        self.dim = dim
        self._vectors: Dict[str, np.ndarray] = {}
        self._metadatas: Dict[str, Dict[str, Any]] = {}

    # ---------------------------------------------------------
    def init_index(self) -> None:  # noqa: D401  pylint: disable=arguments-differ
        # nothing to init in memory impl
        pass

    # ---------------------------------------------------------
    async def upsert_embeddings(
        self,
        embeddings: List[np.ndarray],
        ids: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not (len(embeddings) == len(ids) == len(metadatas)):
            raise ValueError("长度不一致，无法 upsert")
        for vec, _id, meta in zip(embeddings, ids, metadatas):
            if vec.shape[-1] != self.dim:
                raise ValueError("向量维度错误")
            self._vectors[_id] = vec.astype(np.float32)
            self._metadatas[_id] = meta

    # ---------------------------------------------------------
    async def query(
        self, query_vector: np.ndarray, top_k: int = 5, **kwargs
    ) -> List[ScoredDocument]:
        if len(self._vectors) == 0:
            return []
        # cosine similarity
        q = query_vector.astype(np.float32)
        q_norm = norm(q)
        scores: List[ScoredDocument] = []
        for _id, vec in self._vectors.items():
            sim = float(np.dot(q, vec) / (q_norm * norm(vec) + 1e-9))
            scores.append(
                ScoredDocument(news_id=_id, score=sim, metadata=self._metadatas[_id])
            )
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k]

    # ---------------------------------------------------------
    async def delete(self, ids: List[str]) -> None:
        for _id in ids:
            self._vectors.pop(_id, None)
            self._metadatas.pop(_id, None) 