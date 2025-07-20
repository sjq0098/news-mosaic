"""向量数据库抽象接口
"""

from typing import List, Dict, Any
from abc import ABC, abstractmethod

from models.embedding import EmbeddingResult


class IVectorDB(ABC):
    """统一向量数据库操作接口，支持 Pinecone / Weaviate / FAISS 等实现"""

    @abstractmethod
    def init_index(self, dimension: int) -> None:
        """确保索引/集合已创建，维度不匹配时应抛出异常"""

    @abstractmethod
    def upsert_embeddings(self, results: List[EmbeddingResult]) -> None:
        """批量写入或更新向量"""

    @abstractmethod
    def query_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """相似度检索，返回 List[{"news_id", "score", "metadata"}]"""

    @abstractmethod
    def delete_by_source(self, source_id: str) -> None:
        """按新闻 ID 删除向量（可选实现）""" 