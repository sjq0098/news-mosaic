"""
简化的导入测试
"""

def test_step_by_step():
    """逐步测试导入"""
    try:
        print("1. 测试基础模块...")
        import sys
        print(f"Python版本: {sys.version}")
        
        print("2. 测试pydantic...")
        from pydantic import BaseModel
        
        print("3. 测试loguru...")
        from loguru import logger
        
        print("4. 测试core.config...")
        from core.config import settings
        
        print("5. 测试core.database...")
        from core.database import Collections
        
        print("6. 测试models.embedding...")
        from models.embedding import EmbeddingResult, TextChunk, ChunkMetadata
        
        print("7. 测试services.news_service...")
        from services.news_service import NewsService
        
        print("8. 测试services.qwen_service...")
        from services.qwen_service import QWENService
        
        print("9. 测试services.news_processing_pipeline...")
        from services.news_processing_pipeline import NewsProcessingPipeline
        
        print("✅ 所有导入成功！")
        
    except Exception as e:
        print(f"❌ 在步骤中失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_step_by_step()
