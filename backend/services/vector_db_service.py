"""向量数据库服务工厂
根据 settings.VECTOR_DB_BACKEND 创建具体实现
"""

from functools import lru_cache
from core.config import settings

from services.vector_db.faiss_db import FaissVectorDB
# 预留：pinecone/weaviate 实现后可按需导入


@lru_cache
def get_vector_db():
    backend = getattr(settings, "VECTOR_DB_BACKEND", "faiss").lower()
    if backend == "faiss":
        return FaissVectorDB()
    # elif backend == "pinecone":
    #     from services.vector_db.pinecone_db import PineconeVectorDB
    #     return PineconeVectorDB()
    # elif backend == "weaviate":
    #     from services.vector_db.weaviate_db import WeaviateVectorDB
    #     return WeaviateVectorDB()
    else:
        raise ValueError(f"Unsupported VECTOR_DB_BACKEND: {backend}") 