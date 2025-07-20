"""
Embedding 相关数据模型
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import numpy as np


class TextChunkModel(BaseModel):
    """文本分块模型"""
    content: str = Field(..., description="分块内容")
    chunk_index: int = Field(..., description="分块序号")
    token_count: int = Field(..., description="token 数量")
    start_pos: int = Field(..., description="原文起始位置")
    end_pos: int = Field(..., description="原文结束位置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class EmbeddingModel(BaseModel):
    """向量模型"""
    vector: List[float] = Field(..., description="向量数据")
    dimension: int = Field(..., description="向量维度")
    model_name: str = Field(..., description="模型名称")
    model_version: str = Field(default="", description="模型版本")


class EmbeddingResultModel(BaseModel):
    """Embedding 结果模型"""
    chunk_id: str = Field(..., description="分块 ID")
    source_id: str = Field(..., description="来源 ID")
    chunk: TextChunkModel = Field(..., description="文本分块")
    embedding: EmbeddingModel = Field(..., description="向量数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    processing_info: Dict[str, Any] = Field(default_factory=dict, description="处理信息")


@dataclass
class TextChunk:
    """文本分块数据类（内部处理用）"""
    content: str
    chunk_index: int
    token_count: int
    start_pos: int
    end_pos: int
    metadata: dict
    
    def to_model(self) -> TextChunkModel:
        """转换为 Pydantic 模型"""
        return TextChunkModel(
            content=self.content,
            chunk_index=self.chunk_index,
            token_count=self.token_count,
            start_pos=self.start_pos,
            end_pos=self.end_pos,
            metadata=self.metadata
        )


@dataclass
class EmbeddingResult:
    """Embedding 结果数据类（内部处理用）"""
    chunk: TextChunk
    embedding: np.ndarray
    model_info: dict
    processing_time: float = 0.0
    
    def to_model(self, chunk_id: str, source_id: str) -> EmbeddingResultModel:
        """转换为 Pydantic 模型"""
        return EmbeddingResultModel(
            chunk_id=chunk_id,
            source_id=source_id,
            chunk=self.chunk.to_model(),
            embedding=EmbeddingModel(
                vector=self.embedding.tolist(),
                dimension=len(self.embedding),
                model_name=self.model_info.get("model", "text-embedding-v3"),
                model_version=self.model_info.get("version", "")
            ),
            processing_info={
                "processing_time": self.processing_time,
                "model_info": self.model_info
            }
        )