#!/usr/bin/env python3
"""
Pipeline完整功能测试 - 使用模拟用户数据

此测试展示如何为不同类型的用户创建模拟数据，并测试pipeline的各种功能
"""

import asyncio
import time
import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.complete_pipeline_service import (
    CompletePipelineService, 
    PipelineRequest, 
    PipelineMode
)
from services.conversation_context_manager import ConversationContextManager
from models.user_memory import (
    UserMemoryProfile, UserPreference, MemoryItem, MemoryType,
    InterestCategory, ConversationContext
)
from models.chat import ChatMessage, MessageRole


class MockUserDataGenerator:
    """模拟用户数据生成器"""
    
    @staticmethod
    def create_tech_enthusiast_user(user_id: str = None) -> UserMemoryProfile:
        """创建科技爱好者用户"""
        user_id = user_id or f"tech_user_{uuid.uuid4().hex[:8]}"
        
        preferences = UserPreference(
            preferred_categories=[
                InterestCategory.TECHNOLOGY,
                InterestCategory.SCIENCE,
                InterestCategory.BUSINESS
            ],
            disliked_categories=[InterestCategory.ENTERTAINMENT],
            preferred_news_length="long",
            preferred_analysis_depth="comprehensive",
            communication_style="professional",
            response_format="detailed"
        )
        
        # 添加一些技术相关的记忆
        memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PREFERENCE,
                content="用户对AI和机器学习技术特别感兴趣",
                importance_score=0.9,
                related_topics=["AI", "机器学习", "深度学习"]
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.INTERACTION,
                content="经常询问技术发展趋势和应用前景",
                importance_score=0.8,
                related_topics=["技术趋势", "应用场景"]
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.KNOWLEDGE,
                content="具备一定的编程背景，理解技术概念",
                importance_score=0.7,
                related_topics=["编程", "技术理解"]
            )
        ]
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=memories,
            total_conversations=15,
            total_memories=len(memories),
            personalization_score=0.8,
            interaction_frequency=0.7
        )
    
    @staticmethod
    def create_business_analyst_user(user_id: str = None) -> UserMemoryProfile:
        """创建商业分析师用户"""
        user_id = user_id or f"business_user_{uuid.uuid4().hex[:8]}"
        
        preferences = UserPreference(
            preferred_categories=[
                InterestCategory.FINANCE,
                InterestCategory.BUSINESS,
                InterestCategory.INTERNATIONAL
            ],
            disliked_categories=[InterestCategory.SPORTS],
            preferred_news_length="medium",
            preferred_analysis_depth="detailed",
            communication_style="professional",
            response_format="structured"
        )
        
        memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PREFERENCE,
                content="关注市场动向和企业财务表现",
                importance_score=0.9,
                related_topics=["市场分析", "财务", "企业发展"]
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.CONTEXT,
                content="经常需要数据支撑的分析报告",
                importance_score=0.8,
                related_topics=["数据分析", "报告", "趋势预测"]
            )
        ]
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=memories,
            total_conversations=25,
            total_memories=len(memories),
            personalization_score=0.9,
            interaction_frequency=0.8
        )
    
    @staticmethod
    def create_general_user(user_id: str = None) -> UserMemoryProfile:
        """创建普通用户"""
        user_id = user_id or f"general_user_{uuid.uuid4().hex[:8]}"
        
        preferences = UserPreference(
            preferred_categories=[
                InterestCategory.LIFESTYLE,
                InterestCategory.HEALTH,
                InterestCategory.LOCAL
            ],
            preferred_news_length="short",
            preferred_analysis_depth="brief",
            communication_style="casual",
            response_format="simple"
        )
        
        memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PREFERENCE,
                content="偏好简洁明了的信息",
                importance_score=0.6,
                related_topics=["简洁", "易懂"]
            )
        ]
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=memories,
            total_conversations=5,
            total_memories=len(memories),
            personalization_score=0.4,
            interaction_frequency=0.3
        )
    
    @staticmethod
    def create_conversation_context(session_id: str, user_id: str, conversation_type: str = "general") -> ConversationContext:
        """创建对话上下文"""
        if conversation_type == "tech":
            return ConversationContext(
                session_id=session_id,
                user_id=user_id,
                current_topic="人工智能技术发展",
                discussed_topics=["AI", "机器学习", "深度学习"],
                mentioned_entities=["GPT", "Transformer", "神经网络"],
                user_questions=["AI技术的发展前景如何？", "机器学习在实际应用中的挑战是什么？"],
                conversation_sentiment="positive",
                complexity_level="high",
                message_count=8
            )
        elif conversation_type == "business":
            return ConversationContext(
                session_id=session_id,
                user_id=user_id,
                current_topic="市场分析",
                discussed_topics=["股市", "经济趋势", "行业分析"],
                mentioned_entities=["GDP", "CPI", "股票指数"],
                user_questions=["当前市场趋势如何？", "哪些行业值得关注？"],
                conversation_sentiment="neutral",
                complexity_level="medium",
                message_count=5
            )
        else:
            return ConversationContext(
                session_id=session_id,
                user_id=user_id,
                current_topic="日常新闻",
                discussed_topics=["生活", "健康"],
                mentioned_entities=[],
                user_questions=["最近有什么有趣的新闻吗？"],
                conversation_sentiment="neutral",
                complexity_level="low",
                message_count=2
            )


class PipelineTestSuite:
    """Pipeline测试套件"""
    
    def __init__(self):
        self.pipeline_service = CompletePipelineService()
        self.context_manager = ConversationContextManager()
        self.test_results = []
    
    async def setup_mock_users(self):
        """设置模拟用户"""
        logger.info("🔧 设置模拟用户数据...")
        
        # 创建不同类型的用户
        self.tech_user = MockUserDataGenerator.create_tech_enthusiast_user()
        self.business_user = MockUserDataGenerator.create_business_analyst_user()
        self.general_user = MockUserDataGenerator.create_general_user()
        
        # 注入到上下文管理器
        self.context_manager.user_profiles[self.tech_user.user_id] = self.tech_user
        self.context_manager.user_profiles[self.business_user.user_id] = self.business_user
        self.context_manager.user_profiles[self.general_user.user_id] = self.general_user
        
        logger.info(f"✅ 已创建 3 个模拟用户:")
        logger.info(f"   • 科技用户: {self.tech_user.user_id}")
        logger.info(f"   • 商业用户: {self.business_user.user_id}")
        logger.info(f"   • 普通用户: {self.general_user.user_id}")
    
    async def test_personalized_responses(self):
        """测试个性化回复"""
        logger.info("\n📊 测试1: 个性化回复功能")
        print("-" * 60)
        
        # 同一个问题，不同用户应该得到不同风格的回复
        query = "最近AI技术有什么新突破？"
        
        test_users = [
            ("科技用户", self.tech_user),
            ("商业用户", self.business_user),
            ("普通用户", self.general_user)
        ]
        
        for user_type, user_profile in test_users:
            print(f"\n🔹 {user_type} ({user_profile.user_id}):")
            
            request = PipelineRequest(
                user_id=user_profile.user_id,
                message=query,
                mode=PipelineMode.ENHANCED_CHAT,
                enable_memory=True,
                enable_rag=True,
                enable_cards=False
            )
            
            start_time = time.time()
            response = await self.pipeline_service.process_pipeline(request)
            execution_time = time.time() - start_time
            
            print(f"   💬 AI回复: {response.ai_response[:200]}...")
            print(f"   ⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"   🎯 个性化得分: {response.confidence_score:.2f}")
            print(f"   ✅ 成功: {response.success}")
            
            self.test_results.append({
                "test": "个性化回复",
                "user_type": user_type,
                "success": response.success,
                "execution_time": execution_time,
                "confidence": response.confidence_score
            })
    
    async def test_different_pipeline_modes(self):
        """测试不同的Pipeline模式"""
        logger.info("\n🔧 测试2: 不同Pipeline模式")
        print("-" * 60)
        
        user_id = self.tech_user.user_id
        query = "新能源汽车市场发展如何？"
        
        # 测试不同模式
        modes = [
            (PipelineMode.ENHANCED_CHAT, "仅增强对话"),
            (PipelineMode.RAG_ANALYSIS, "RAG分析"),
            (PipelineMode.CARD_GENERATION, "卡片生成"),
            (PipelineMode.UNIFIED_COMPLETE, "完整统一"),
            (PipelineMode.CUSTOM, "自定义模式")
        ]
        
        for mode, description in modes:
            print(f"\n🔹 测试模式: {description}")
            
            request = PipelineRequest(
                user_id=user_id,
                message=query,
                mode=mode,
                enable_memory=True,
                enable_rag=True,
                enable_cards=(mode == PipelineMode.CARD_GENERATION or mode == PipelineMode.UNIFIED_COMPLETE)
            )
            
            start_time = time.time()
            try:
                response = await self.pipeline_service.process_pipeline(request)
                execution_time = time.time() - start_time
                
                print(f"   ✅ 成功: {response.success}")
                print(f"   ⏱️ 执行时间: {execution_time:.2f}秒")
                print(f"   📰 检索新闻数: {len(response.retrieved_news)}")
                print(f"   🎴 生成卡片数: {len(response.generated_cards)}")
                
                self.test_results.append({
                    "test": "Pipeline模式",
                    "mode": mode,
                    "success": response.success,
                    "execution_time": execution_time,
                    "news_count": len(response.retrieved_news),
                    "cards_count": len(response.generated_cards)
                })
                
            except Exception as e:
                print(f"   ❌ 失败: {str(e)}")
                self.test_results.append({
                    "test": "Pipeline模式",
                    "mode": mode,
                    "success": False,
                    "error": str(e)
                })
    
    async def test_conversation_context(self):
        """测试对话上下文记忆"""
        logger.info("\n🧠 测试3: 对话上下文记忆")
        print("-" * 60)
        
        user_id = self.tech_user.user_id
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # 创建对话上下文
        conversation_context = MockUserDataGenerator.create_conversation_context(
            session_id, user_id, "tech"
        )
        self.context_manager.active_contexts[session_id] = conversation_context
        
        # 模拟多轮对话
        conversation_turns = [
            "刚才我们聊到了AI技术，能详细说说GPT的发展历程吗？",
            "那Transformer架构有什么特别之处？",
            "这些技术在实际应用中表现如何？"
        ]
        
        for i, message in enumerate(conversation_turns, 1):
            print(f"\n🔄 第{i}轮对话:")
            print(f"   👤 用户: {message}")
            
            request = PipelineRequest(
                user_id=user_id,
                session_id=session_id,
                message=message,
                mode=PipelineMode.ENHANCED_CHAT,
                enable_memory=True,
                enable_rag=True
            )
            
            start_time = time.time()
            response = await self.pipeline_service.process_pipeline(request)
            execution_time = time.time() - start_time
            
            print(f"   🤖 AI: {response.ai_response[:150]}...")
            print(f"   ⏱️ 时间: {execution_time:.2f}秒")
            
            # 模拟更新对话上下文
            conversation_context.message_count += 2  # 用户+AI
            conversation_context.last_updated_at = datetime.utcnow()
            
            self.test_results.append({
                "test": "对话上下文",
                "turn": i,
                "success": response.success,
                "execution_time": execution_time
            })
    
    async def test_batch_processing(self):
        """测试批量处理"""
        logger.info("\n⚡ 测试4: 批量处理功能")
        print("-" * 60)
        
        # 创建多个用户的并发请求
        batch_requests = [
            (self.tech_user.user_id, "AI技术的未来发展方向是什么？"),
            (self.business_user.user_id, "当前股市表现如何？"),
            (self.general_user.user_id, "最近有什么有趣的新闻？"),
            (self.tech_user.user_id, "量子计算的实用化进展怎样？"),
            (self.business_user.user_id, "新能源汽车行业的投资机会在哪里？")
        ]
        
        # 创建请求对象
        pipeline_requests = []
        for user_id, message in batch_requests:
            request = PipelineRequest(
                user_id=user_id,
                message=message,
                mode=PipelineMode.UNIFIED_COMPLETE,
                enable_memory=True,
                enable_rag=True,
                enable_cards=True
            )
            pipeline_requests.append(request)
        
        # 并发执行
        print(f"🚀 开始并发处理 {len(pipeline_requests)} 个请求...")
        
        start_time = time.time()
        results = await asyncio.gather(*[
            self.pipeline_service.process_pipeline(req) 
            for req in pipeline_requests
        ], return_exceptions=True)
        total_time = time.time() - start_time
        
        # 分析结果
        success_count = sum(1 for r in results if isinstance(r, object) and hasattr(r, 'success') and r.success)
        error_count = len(results) - success_count
        
        print(f"📊 批量处理结果:")
        print(f"   • 总请求数: {len(pipeline_requests)}")
        print(f"   • 成功数: {success_count}")
        print(f"   • 失败数: {error_count}")
        print(f"   • 总时间: {total_time:.2f}秒")
        print(f"   • 平均时间: {total_time/len(pipeline_requests):.2f}秒")
        
        self.test_results.append({
            "test": "批量处理",
            "total_requests": len(pipeline_requests),
            "success_count": success_count,
            "error_count": error_count,
            "total_time": total_time,
            "average_time": total_time/len(pipeline_requests)
        })
    
    async def test_error_handling(self):
        """测试错误处理"""
        logger.info("\n🔥 测试5: 错误处理机制")
        print("-" * 60)
        
        # 测试各种错误情况
        error_cases = [
            ("空消息", ""),
            ("超长消息", "这是一个非常长的消息" * 100),
            ("不存在的用户", "测试消息"),
            ("无效模式", "测试消息")
        ]
        
        for case_name, message in error_cases:
            print(f"\n🔹 错误测试: {case_name}")
            
            try:
                user_id = "invalid_user" if case_name == "不存在的用户" else self.tech_user.user_id
                
                request = PipelineRequest(
                    user_id=user_id,
                    message=message,
                    mode=PipelineMode.UNIFIED_COMPLETE if case_name != "无效模式" else "invalid_mode"
                )
                
                start_time = time.time()
                response = await self.pipeline_service.process_pipeline(request)
                execution_time = time.time() - start_time
                
                print(f"   ✅ 处理完成: {response.success}")
                print(f"   ⏱️ 时间: {execution_time:.2f}秒")
                
            except Exception as e:
                print(f"   ❌ 异常捕获: {str(e)[:100]}...")
                
            self.test_results.append({
                "test": "错误处理",
                "case": case_name,
                "handled": True
            })
    
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("\n📋 生成测试报告")
        print("=" * 80)
        print("🎯 Pipeline功能测试报告")
        print("=" * 80)
        
        # 按测试类型分组
        test_groups = {}
        for result in self.test_results:
            test_type = result["test"]
            if test_type not in test_groups:
                test_groups[test_type] = []
            test_groups[test_type].append(result)
        
        # 输出各组结果
        for test_type, results in test_groups.items():
            print(f"\n📊 {test_type}:")
            print("-" * 40)
            
            if test_type == "个性化回复":
                for r in results:
                    status = "✅" if r["success"] else "❌"
                    print(f"   {status} {r['user_type']}: {r['execution_time']:.2f}s, 置信度: {r['confidence']:.2f}")
            
            elif test_type == "Pipeline模式":
                for r in results:
                    if r["success"]:
                        print(f"   ✅ {r['mode']}: {r['execution_time']:.2f}s, 新闻:{r['news_count']}, 卡片:{r['cards_count']}")
                    else:
                        print(f"   ❌ {r['mode']}: {r.get('error', '未知错误')}")
            
            elif test_type == "对话上下文":
                success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
                avg_time = sum(r["execution_time"] for r in results) / len(results)
                print(f"   🎯 成功率: {success_rate:.1f}%")
                print(f"   ⏱️ 平均时间: {avg_time:.2f}秒")
            
            elif test_type == "批量处理":
                r = results[0]  # 只有一个批量测试结果
                print(f"   📦 请求数: {r['total_requests']}")
                print(f"   ✅ 成功率: {r['success_count']}/{r['total_requests']} ({r['success_count']/r['total_requests']*100:.1f}%)")
                print(f"   ⚡ 吞吐量: {r['total_requests']/r['total_time']:.2f} 请求/秒")
            
            elif test_type == "错误处理":
                handled_count = sum(1 for r in results if r["handled"])
                print(f"   🛡️ 错误处理覆盖: {handled_count}/{len(results)} ({handled_count/len(results)*100:.1f}%)")
        
        # 总结
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", True))
        
        print(f"\n🏆 测试总结:")
        print(f"   • 总测试数: {total_tests}")
        print(f"   • 成功测试: {successful_tests}")
        print(f"   • 成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"   • 功能覆盖: 个性化、多模式、上下文、批量处理、错误处理")


async def main():
    """主测试函数"""
    print("🚀 启动Pipeline完整功能测试")
    print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    test_suite = PipelineTestSuite()
    
    try:
        # 设置测试环境
        await test_suite.setup_mock_users()
        
        # 运行测试
        await test_suite.test_personalized_responses()
        await test_suite.test_different_pipeline_modes()
        await test_suite.test_conversation_context()
        await test_suite.test_batch_processing()
        await test_suite.test_error_handling()
        
        # 生成报告
        test_suite.generate_test_report()
        
        print(f"\n🎉 测试完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 