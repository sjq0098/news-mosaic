"""vector_db/base.py
向量数据库通用抽象接口，方便切换 Pinecone / Weaviate / Memory 等实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np

# ---- 数据结构 -------------------------------------------------------------

@dataclass
class ScoredDocument:
    """向量检索返回的文档条目"""
    news_id: str
    score: float
    metadata: Dict[str, Any]


# ---- 抽象接口 -------------------------------------------------------------

class IVectorDB(ABC):
    """向量数据库操作统一接口"""

    @abstractmethod
    def init_index(self) -> None:
        """确保索引/集合存在，如不存在则创建。"""

    @abstractmethod
    async def upsert_embeddings(self, embeddings: List[np.ndarray], ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """批量写入/更新向量。length of three lists must match."""

    @abstractmethod
    async def query(self, query_vector: np.ndarray, top_k: int = 5, **kwargs) -> List[ScoredDocument]:
        """按向量相似度检索，返回 TopK ScoredDocument"""

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """根据文档 id 删除向量。""" 