"""
Embedding API 端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from services.embedding_service import embedding_service
from models.embedding import EmbeddingResultModel


router = APIRouter(prefix="/embedding", tags=["embedding"])


class TextProcessRequest(BaseModel):
    """文本处理请求"""
    text: str = Field(..., description="待处理的文本")
    source_id: str = Field(..., description="来源 ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class BatchTextProcessRequest(BaseModel):
    """批量文本处理请求"""
    texts: List[str] = Field(..., description="文本列表")
    source_ids: List[str] = Field(..., description="来源 ID 列表")
    metadatas: Optional[List[Dict[str, Any]]] = Field(default=None, description="元数据列表")


class ChunkTextRequest(BaseModel):
    """文本分块请求"""
    text: str = Field(..., description="待分块的文本")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


@router.post("/process", response_model=List[EmbeddingResultModel])
async def process_text(request: TextProcessRequest):
    """处理单个文本：分块 + 生成 embeddings"""
    try:
        results = await embedding_service.process_text(
            text=request.text,
            source_id=request.source_id,
            metadata=request.metadata
        )
        
        # 转换为响应模型
        response_results = []
        for result in results:
            chunk_id = f"{request.source_id}_chunk_{result.chunk.chunk_index}"
            response_results.append(
                result.to_model(chunk_id=chunk_id, source_id=request.source_id)
            )
        
        return response_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")


@router.post("/process_batch", response_model=List[List[EmbeddingResultModel]])
async def process_texts_batch(request: BatchTextProcessRequest):
    """批量处理文本"""
    try:
        results = await embedding_service.process_texts_batch(
            texts=request.texts,
            source_ids=request.source_ids,
            metadatas=request.metadatas
        )
        
        # 转换为响应模型
        response_results = []
        for source_results, source_id in zip(results, request.source_ids):
            source_response = []
            for result in source_results:
                chunk_id = f"{source_id}_chunk_{result.chunk.chunk_index}"
                source_response.append(
                    result.to_model(chunk_id=chunk_id, source_id=source_id)
                )
            response_results.append(source_response)
        
        return response_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")


@router.post("/chunk")
async def chunk_text(request: ChunkTextRequest):
    """仅进行文本分块"""
    try:
        chunks = await embedding_service.chunk_text(
            text=request.text,
            metadata=request.metadata
        )
        
        return {
            "chunks": [chunk.to_model() for chunk in chunks],
            "total_chunks": len(chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本分块失败: {str(e)}")


@router.get("/model_info")
async def get_model_info():
    """获取模型信息"""
    try:
        info = await embedding_service.get_model_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")