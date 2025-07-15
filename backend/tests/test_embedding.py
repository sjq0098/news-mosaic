"""
Embedding 服务测试
"""

import asyncio
import sys
import os
# 将 backend 目录放到 sys.path 首位，确保优先使用本地 services 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.embedding_service import embedding_service



async def test_embedding_service():
    """测试 embedding 服务"""
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
    它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
    
    机器学习是人工智能的一个重要分支，它是一种让计算机系统自动学习和改进的方法，
    无需被明确编程。机器学习算法通过分析大量数据来识别模式，并使用这些模式来做出预测或决策。
    
    深度学习是机器学习的一个子集，它使用人工神经网络来模拟人脑的工作方式。
    深度学习在图像识别、语音识别、自然语言处理等领域取得了显著的成果。
    """
    
    # 测试元数据
    metadata = {
        "title": "人工智能介绍",
        "category": "technology",
        "author": "测试作者",
        "published_at": "2024-01-01T00:00:00Z"
    }
    
    try:
        print("🔄 开始测试 embedding 服务...")
        
        # 1. 测试文本分块
        print("\n📝 测试文本分块...")
        chunks = await embedding_service.chunk_text(test_text, metadata)
        print(f"分块数量: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"分块 {i}: {chunk.token_count} tokens, 长度: {len(chunk.content)} 字符")
            print(f"内容预览: {chunk.content[:100]}...")
        
        # 2. 测试完整处理
        print("\n🚀 测试完整处理...")
        results = await embedding_service.process_text(
            text=test_text,
            source_id="test_001",
            metadata=metadata
        )
        
        print(f"处理结果: {len(results)} 个向量")
        for i, result in enumerate(results):
            print(f"向量 {i}: 维度 {len(result.embedding)}, 处理时间: {result.processing_time:.3f}s")
        
        # 3. 测试批量处理
        print("\n⚡ 测试批量处理...")
        batch_results = await embedding_service.process_texts_batch(
            texts=[test_text, "这是第二个测试文本。"],
            source_ids=["test_001", "test_002"],
            metadatas=[metadata, {"title": "测试文本2"}]
        )
        
        print(f"批量处理结果: {len(batch_results)} 个文本")
        for i, text_results in enumerate(batch_results):
            print(f"文本 {i}: {len(text_results)} 个向量")
        
        # 4. 获取模型信息
        print("\n📊 模型信息:")
        model_info = await embedding_service.get_model_info()
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise
    finally:
        await embedding_service.close()


if __name__ == "__main__":
    asyncio.run(test_embedding_service())
