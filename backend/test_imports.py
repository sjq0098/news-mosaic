"""
测试导入是否正常
"""

def test_imports():
    """测试所有新增模块的导入"""
    try:
        print("测试 embedding 模型导入...")
        from models.embedding import EmbeddingResult, TextChunk, ChunkMetadata
        print("✅ embedding 模型导入成功")
        
        print("测试新闻处理流水线导入...")
        from services.news_processing_pipeline import (
            NewsProcessingPipeline, 
            NewsProcessingRequest,
            NewsProcessingResponse
        )
        print("✅ 新闻处理流水线导入成功")
        
        print("测试增强RAG对话服务导入...")
        from services.enhanced_rag_chat_service import (
            EnhancedRAGChatService,
            RAGChatRequest,
            RAGChatResponse
        )
        print("✅ 增强RAG对话服务导入成功")
        
        print("测试用户记忆服务导入...")
        from services.user_memory_service import (
            UserMemoryService,
            UserMemoryRequest,
            UserMemoryResponse
        )
        print("✅ 用户记忆服务导入成功")
        
        print("测试API路由导入...")
        from api.news_pipeline import router as news_pipeline_router
        from api.enhanced_chat import router as enhanced_chat_router
        from api.user_memory import router as user_memory_router
        print("✅ API路由导入成功")
        
        print("\n🎉 所有导入测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


if __name__ == "__main__":
    test_imports()
