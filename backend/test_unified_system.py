"""
统一新闻处理系统集成测试
测试所有重构后的功能是否正常协同工作
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import json

from services.news_processing_pipeline import (
    NewsProcessingPipeline, 
    NewsProcessingRequest,
    get_news_pipeline
)
from services.enhanced_rag_chat_service import (
    EnhancedRAGChatService,
    RAGChatRequest,
    get_enhanced_rag_chat_service
)
from services.user_memory_service import (
    UserMemoryService,
    UserMemoryRequest,
    PersonalizationRequest,
    get_user_memory_service
)
from core.database import init_database, close_database
from core.cache import init_redis, close_redis


class UnifiedSystemTester:
    """统一系统测试器"""
    
    def __init__(self):
        self.test_user_id = "test_user_001"
        self.test_results = []
        
    async def setup(self):
        """测试环境设置"""
        print("🔧 初始化测试环境...")
        await init_database()
        await init_redis()
        print("✅ 测试环境初始化完成")
    
    async def cleanup(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        await close_database()
        await close_redis()
        print("✅ 测试环境清理完成")
    
    async def test_news_processing_pipeline(self):
        """测试新闻处理流水线"""
        print("\n📰 测试新闻处理流水线...")
        
        try:
            pipeline = await get_news_pipeline()
            
            # 创建测试请求
            request = NewsProcessingRequest(
                query="人工智能最新发展",
                user_id=self.test_user_id,
                num_results=5,
                enable_storage=True,
                enable_vectorization=True,
                enable_ai_analysis=True,
                enable_card_generation=True,
                enable_sentiment_analysis=True,
                enable_user_memory=True,
                max_cards=3
            )
            
            # 执行流水线
            start_time = time.time()
            response = await pipeline.process_news_pipeline(request)
            processing_time = time.time() - start_time
            
            # 验证结果
            assert response.success, f"流水线执行失败: {response.message}"
            assert response.total_found > 0, "未找到新闻"
            assert len(response.stage_results) > 0, "缺少阶段结果"
            
            self.test_results.append({
                "test": "news_processing_pipeline",
                "success": True,
                "processing_time": processing_time,
                "total_found": response.total_found,
                "cards_generated": response.cards_generated,
                "stages_completed": len(response.stage_results)
            })
            
            print(f"✅ 新闻处理流水线测试通过")
            print(f"   - 处理时间: {processing_time:.2f}s")
            print(f"   - 找到新闻: {response.total_found}条")
            print(f"   - 生成卡片: {response.cards_generated}张")
            print(f"   - 完成阶段: {len(response.stage_results)}个")
            
            return response
            
        except Exception as e:
            print(f"❌ 新闻处理流水线测试失败: {e}")
            self.test_results.append({
                "test": "news_processing_pipeline",
                "success": False,
                "error": str(e)
            })
            raise
    
    async def test_enhanced_rag_chat(self):
        """测试增强RAG对话"""
        print("\n🤖 测试增强RAG对话...")
        
        try:
            chat_service = await get_enhanced_rag_chat_service()
            
            # 创建测试请求
            request = RAGChatRequest(
                user_id=self.test_user_id,
                message="请分析一下人工智能领域的最新发展趋势",
                max_context_news=3,
                similarity_threshold=0.6,
                use_user_memory=True,
                enable_personalization=True
            )
            
            # 执行对话
            start_time = time.time()
            response = await chat_service.chat_with_rag(request)
            processing_time = time.time() - start_time
            
            # 验证结果
            assert response.success, f"RAG对话失败: {response.message}"
            assert len(response.ai_response) > 0, "AI回复为空"
            assert response.confidence_score > 0, "置信度分数异常"
            
            self.test_results.append({
                "test": "enhanced_rag_chat",
                "success": True,
                "processing_time": processing_time,
                "response_length": len(response.ai_response),
                "confidence_score": response.confidence_score,
                "sources_count": response.sources_count
            })
            
            print(f"✅ 增强RAG对话测试通过")
            print(f"   - 处理时间: {processing_time:.2f}s")
            print(f"   - 回复长度: {len(response.ai_response)}字符")
            print(f"   - 置信度: {response.confidence_score:.2f}")
            print(f"   - 参考来源: {response.sources_count}个")
            
            return response
            
        except Exception as e:
            print(f"❌ 增强RAG对话测试失败: {e}")
            self.test_results.append({
                "test": "enhanced_rag_chat",
                "success": False,
                "error": str(e)
            })
            raise
    
    async def test_user_memory_system(self):
        """测试用户记忆系统"""
        print("\n🧠 测试用户记忆系统...")
        
        try:
            memory_service = await get_user_memory_service()
            
            # 测试行为记录
            behavior_request = UserMemoryRequest(
                user_id=self.test_user_id,
                action="search",
                content="人工智能 机器学习 深度学习",
                metadata={"target_id": "test_search_001"}
            )
            
            start_time = time.time()
            behavior_response = await memory_service.record_user_behavior(behavior_request)
            
            # 测试个性化推荐
            personalization_request = PersonalizationRequest(
                user_id=self.test_user_id,
                query="科技新闻",
                max_recommendations=5
            )
            
            personalization_response = await memory_service.get_personalized_content(personalization_request)
            processing_time = time.time() - start_time
            
            # 验证结果
            assert behavior_response.success, f"行为记录失败: {behavior_response.message}"
            assert personalization_response.success, "个性化推荐失败"
            
            self.test_results.append({
                "test": "user_memory_system",
                "success": True,
                "processing_time": processing_time,
                "interests_updated": behavior_response.interests_updated,
                "recommendations_count": len(personalization_response.recommendations),
                "personalization_score": behavior_response.personalization_score
            })
            
            print(f"✅ 用户记忆系统测试通过")
            print(f"   - 处理时间: {processing_time:.2f}s")
            print(f"   - 兴趣更新: {behavior_response.interests_updated}")
            print(f"   - 推荐数量: {len(personalization_response.recommendations)}个")
            print(f"   - 个性化分数: {behavior_response.personalization_score:.2f}")
            
            return behavior_response, personalization_response
            
        except Exception as e:
            print(f"❌ 用户记忆系统测试失败: {e}")
            self.test_results.append({
                "test": "user_memory_system",
                "success": False,
                "error": str(e)
            })
            raise
    
    async def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        print("\n🔄 测试端到端工作流...")
        
        try:
            # 1. 新闻处理流水线
            pipeline_response = await self.test_news_processing_pipeline()
            
            # 2. 基于处理结果进行对话
            if pipeline_response.ai_summary:
                chat_service = await get_enhanced_rag_chat_service()
                chat_request = RAGChatRequest(
                    user_id=self.test_user_id,
                    message=f"基于刚才的分析，{pipeline_response.query}领域还有哪些值得关注的发展方向？",
                    use_user_memory=True,
                    enable_personalization=True
                )
                
                chat_response = await chat_service.chat_with_rag(chat_request)
                assert chat_response.success, "端到端对话失败"
            
            # 3. 记录用户行为
            memory_service = await get_user_memory_service()
            memory_request = UserMemoryRequest(
                user_id=self.test_user_id,
                action="like",
                content=pipeline_response.query,
                metadata={"pipeline_id": pipeline_response.pipeline_id}
            )
            
            memory_response = await memory_service.record_user_behavior(memory_request)
            assert memory_response.success, "行为记录失败"
            
            print(f"✅ 端到端工作流测试通过")
            print(f"   - 流水线 → 对话 → 记忆 全流程协同工作正常")
            
            self.test_results.append({
                "test": "end_to_end_workflow",
                "success": True,
                "workflow_steps": 3
            })
            
        except Exception as e:
            print(f"❌ 端到端工作流测试失败: {e}")
            self.test_results.append({
                "test": "end_to_end_workflow",
                "success": False,
                "error": str(e)
            })
            raise
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始统一新闻处理系统集成测试")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            await self.setup()
            
            # 运行各项测试
            await self.test_news_processing_pipeline()
            await self.test_enhanced_rag_chat()
            await self.test_user_memory_system()
            await self.test_end_to_end_workflow()
            
        except Exception as e:
            print(f"\n💥 测试过程中发生错误: {e}")
        
        finally:
            await self.cleanup()
        
        # 生成测试报告
        total_time = time.time() - start_time
        self.generate_test_report(total_time)
    
    def generate_test_report(self, total_time: float):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        print(f"总耗时: {total_time:.2f}s")
        
        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if not result["success"]:
                print(f"   错误: {result.get('error', '未知错误')}")
        
        # 保存测试结果到文件
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_time": total_time,
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细测试结果已保存到 test_results.json")


async def main():
    """主函数"""
    tester = UnifiedSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
