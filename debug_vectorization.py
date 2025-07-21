#!/usr/bin/env python3
"""
调试向量化问题的详细脚本
"""

import asyncio
import requests
import json
import time
import sys
import os

# 添加后端路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 测试配置
BASE_URL = "http://localhost:8000"

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

async def test_embedding_service():
    """直接测试embedding服务"""
    print("\n🔍 直接测试Embedding服务...")
    
    try:
        from services.embedding_service import QWenEmbeddingService
        from core.config import settings
        
        print(f"QWEN_API_KEY配置: {settings.QWEN_API_KEY[:10]}..." if settings.QWEN_API_KEY else "未配置")
        print(f"API配置状态: {settings.is_api_configured('qwen')}")
        
        embedding_service = QWenEmbeddingService()
        print(f"Embedding服务演示模式: {embedding_service.demo_mode}")
        
        # 测试生成向量
        test_text = "这是一个测试文本"
        print(f"测试文本: {test_text}")
        
        embeddings = await embedding_service.get_embeddings([test_text])
        print(f"生成向量数量: {len(embeddings)}")
        if embeddings:
            print(f"向量维度: {len(embeddings[0])}")
            print(f"向量前5个值: {embeddings[0][:5]}")
            return True
        else:
            print("❌ 向量生成失败")
            return False
            
    except Exception as e:
        print(f"❌ Embedding服务测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

async def test_vector_db():
    """测试向量数据库"""
    print("\n🗄️ 测试向量数据库...")
    
    try:
        from services.vector_db_service import get_vector_db
        from models.embedding import EmbeddingResult, TextChunk, ChunkMetadata
        
        vector_db = get_vector_db()
        print(f"向量数据库类型: {type(vector_db).__name__}")
        
        # 初始化索引
        vector_db.init_index(1536)
        print("✅ 向量数据库初始化成功")
        
        # 创建测试向量
        test_chunk = TextChunk(
            content="测试新闻内容",
            chunk_index=0,
            metadata=ChunkMetadata(
                source_id="test_id",
                title="测试标题",
                published_at="2024-01-01",
                source="测试来源"
            )
        )
        
        # 生成测试向量
        import numpy as np
        test_vector = np.random.normal(0, 1, 1536).astype(np.float32)
        test_vector = test_vector / np.linalg.norm(test_vector)
        
        embedding_result = EmbeddingResult(
            chunk=test_chunk,
            embedding=test_vector.tolist(),
            model_info={"source_id": "test_id"}
        )
        
        # 存储向量
        vector_db.upsert_embeddings([embedding_result])
        print("✅ 测试向量存储成功")
        
        # 查询向量
        results = vector_db.query_similar("测试查询", top_k=1)
        print(f"查询结果数量: {len(results)}")
        if results:
            print(f"查询结果: {results[0]}")
            return True
        else:
            print("❌ 向量查询失败")
            return False
            
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_news_processing_with_debug():
    """测试新闻处理（带调试）"""
    print("\n📰 测试新闻处理（启用详细日志）...")
    
    news_request = {
        "query": "人工智能",
        "num_results": 3,  # 减少数量以便调试
        "enable_storage": True,
        "enable_vectorization": True,
        "enable_ai_analysis": False,  # 暂时关闭AI分析
        "enable_card_generation": False,  # 暂时关闭卡片生成
        "enable_sentiment_analysis": False,  # 暂时关闭情感分析
        "enable_user_memory": False
    }
    
    try:
        print("发送新闻处理请求...")
        response = requests.post(
            f"{BASE_URL}/api/news-pipeline/process",
            json=news_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 新闻处理响应:")
            print(f"   - 成功状态: {result.get('success', False)}")
            print(f"   - 找到新闻: {result.get('total_found', 0)} 条")
            print(f"   - 处理数量: {result.get('processed_count', 0)} 条")
            print(f"   - 创建向量: {result.get('vectors_created', 0)} 个")
            
            # 检查阶段结果
            stage_results = result.get('stage_results', [])
            print(f"\n📊 处理阶段详情:")
            for stage in stage_results:
                stage_name = stage.get('stage', 'unknown')
                success = stage.get('success', False)
                error = stage.get('error', '')
                print(f"   - {stage_name}: {'✅' if success else '❌'} {error if error else ''}")
            
            return result.get('vectors_created', 0) > 0
            
        else:
            print(f"❌ 新闻处理失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 新闻处理异常: {e}")
        return False

def test_rag_chat():
    """测试RAG对话"""
    print("\n🤖 测试RAG对话...")
    
    chat_request = {
        "user_id": "test_user",
        "message": "刚刚搜索到的人工智能新闻有什么重要内容？",
        "max_context_news": 5,
        "similarity_threshold": 0.3,  # 降低阈值
        "use_user_memory": False,  # 暂时关闭用户记忆
        "enable_personalization": False  # 暂时关闭个性化
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-chat/chat",
            json=chat_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RAG对话响应:")
            print(f"   - 成功状态: {result.get('success', False)}")
            print(f"   - 置信度: {result.get('confidence_score', 0):.1%}")
            print(f"   - 来源数量: {result.get('sources_count', 0)} 条新闻")
            print(f"   - AI回复: {result.get('ai_response', '')[:100]}...")
            
            return result.get('sources_count', 0) > 0
            
        else:
            print(f"❌ RAG对话失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAG对话异常: {e}")
        return False

async def main():
    """主调试函数"""
    print("🔧 开始详细调试向量化问题...")
    print("=" * 60)
    
    # 1. 检查后端服务
    if not test_api_health():
        print("\n❌ 后端服务不可用，请先启动后端服务")
        return
    
    # 2. 测试Embedding服务
    embedding_ok = await test_embedding_service()
    
    # 3. 测试向量数据库
    vector_db_ok = await test_vector_db()
    
    # 4. 测试新闻处理
    if embedding_ok and vector_db_ok:
        print("\n✅ 基础服务测试通过，开始测试完整流程...")
        vectorization_ok = test_news_processing_with_debug()
        
        if vectorization_ok:
            print("\n✅ 向量化成功，测试RAG对话...")
            time.sleep(2)  # 等待向量化完成
            rag_ok = test_rag_chat()
            
            if rag_ok:
                print("\n🎉 RAG对话修复成功！")
            else:
                print("\n❌ RAG对话仍有问题")
        else:
            print("\n❌ 向量化失败")
    else:
        print("\n❌ 基础服务有问题，无法继续测试")
    
    print("\n" + "=" * 60)
    print("🔧 调试完成")

if __name__ == "__main__":
    asyncio.run(main())
