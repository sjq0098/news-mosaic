#!/usr/bin/env python3
"""
简化的Pipeline测试演示 - 展示如何快速上手模拟用户数据测试

这个文件展示了最基本的模拟用户数据使用方法，适合快速理解和学习
"""

import asyncio
import uuid
import sys
import os
from datetime import datetime
from loguru import logger

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.complete_pipeline_service import CompletePipelineService, PipelineRequest, PipelineMode
from models.user_memory import UserMemoryProfile, UserPreference, MemoryItem, MemoryType, InterestCategory


class SimpleUserMockFactory:
    """简单的用户模拟工厂"""
    
    @staticmethod
    def create_test_user(
        user_type: str = "tech", 
        user_id: str = None
    ) -> UserMemoryProfile:
        """
        创建测试用户
        
        Args:
            user_type: 用户类型 ("tech", "business", "general")
            user_id: 指定用户ID（可选）
        
        Returns:
            UserMemoryProfile: 用户档案
        """
        user_id = user_id or f"test_{user_type}_{uuid.uuid4().hex[:6]}"
        
        if user_type == "tech":
            return SimpleUserMockFactory._create_tech_user(user_id)
        elif user_type == "business":
            return SimpleUserMockFactory._create_business_user(user_id)
        else:
            return SimpleUserMockFactory._create_general_user(user_id)
    
    @staticmethod
    def _create_tech_user(user_id: str) -> UserMemoryProfile:
        """创建科技用户"""
        preferences = UserPreference(
            preferred_categories=[InterestCategory.TECHNOLOGY, InterestCategory.SCIENCE],
            communication_style="professional",
            response_format="detailed"
        )
        
        memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PREFERENCE,
                content="喜欢深入的技术分析",
                importance_score=0.8
            )
        ]
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=memories,
            personalization_score=0.8
        )
    
    @staticmethod
    def _create_business_user(user_id: str) -> UserMemoryProfile:
        """创建商业用户"""
        preferences = UserPreference(
            preferred_categories=[InterestCategory.FINANCE, InterestCategory.BUSINESS],
            communication_style="professional",
            response_format="structured"
        )
        
        memories = [
            MemoryItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PREFERENCE,
                content="关注市场趋势和商业机会",
                importance_score=0.9
            )
        ]
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=memories,
            personalization_score=0.9
        )
    
    @staticmethod
    def _create_general_user(user_id: str) -> UserMemoryProfile:
        """创建普通用户"""
        preferences = UserPreference(
            preferred_categories=[InterestCategory.LIFESTYLE],
            communication_style="casual",
            response_format="simple"
        )
        
        return UserMemoryProfile(
            user_id=user_id,
            preferences=preferences,
            memories=[],
            personalization_score=0.3
        )


async def test_basic_pipeline():
    """基础Pipeline测试"""
    print("🚀 开始基础Pipeline测试")
    print("=" * 50)
    
    # 1. 创建pipeline服务
    pipeline_service = CompletePipelineService()
    
    # 2. 创建测试用户
    test_user = SimpleUserMockFactory.create_test_user("tech")
    logger.info(f"创建测试用户: {test_user.user_id}")
    
    # 3. 注入用户数据到服务
    pipeline_service.context_manager.user_profiles[test_user.user_id] = test_user
    
    # 4. 创建测试请求
    request = PipelineRequest(
        user_id=test_user.user_id,
        message="最近AI技术有什么发展？",
        mode=PipelineMode.ENHANCED_CHAT
    )
    
    # 5. 执行测试
    print(f"📝 测试查询: {request.message}")
    print(f"👤 用户类型: 科技爱好者")
    print(f"🔧 处理模式: {request.mode}")
    
    try:
        response = await pipeline_service.process_pipeline(request)
        
        print(f"\n✅ 测试结果:")
        print(f"   • 处理成功: {response.success}")
        print(f"   • 执行时间: {response.total_execution_time:.2f}秒")
        print(f"   • AI回复: {response.ai_response[:100]}...")
        print(f"   • 置信度: {response.confidence_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_different_user_types():
    """测试不同用户类型"""
    print("\n🎭 测试不同用户类型的个性化回复")
    print("=" * 50)
    
    pipeline_service = CompletePipelineService()
    query = "新能源汽车发展怎么样？"
    
    # 测试不同类型用户
    user_types = ["tech", "business", "general"]
    
    for user_type in user_types:
        print(f"\n🔹 测试 {user_type} 用户:")
        
        # 创建用户
        user = SimpleUserMockFactory.create_test_user(user_type)
        pipeline_service.context_manager.user_profiles[user.user_id] = user
        
        # 创建请求
        request = PipelineRequest(
            user_id=user.user_id,
            message=query,
            mode=PipelineMode.ENHANCED_CHAT,
            enable_memory=True
        )
        
        try:
            response = await pipeline_service.process_pipeline(request)
            
            print(f"   💬 回复风格: {user.preferences.communication_style}")
            print(f"   📄 回复格式: {user.preferences.response_format}")
            print(f"   🎯 个性化分数: {user.personalization_score}")
            print(f"   ✅ 处理成功: {response.success}")
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")


async def test_pipeline_modes():
    """测试不同Pipeline模式"""
    print("\n⚙️ 测试不同Pipeline模式")
    print("=" * 50)
    
    pipeline_service = CompletePipelineService()
    user = SimpleUserMockFactory.create_test_user("tech")
    pipeline_service.context_manager.user_profiles[user.user_id] = user
    
    # 测试不同模式
    modes = [
        (PipelineMode.ENHANCED_CHAT, "增强对话"),
        (PipelineMode.RAG_ANALYSIS, "RAG分析"),
        (PipelineMode.UNIFIED_COMPLETE, "完整处理")
    ]
    
    for mode, description in modes:
        print(f"\n🔧 测试模式: {description}")
        
        request = PipelineRequest(
            user_id=user.user_id,
            message="量子计算有什么新进展？",
            mode=mode
        )
        
        try:
            response = await pipeline_service.process_pipeline(request)
            
            print(f"   ✅ 成功: {response.success}")
            print(f"   📰 新闻数: {len(response.retrieved_news)}")
            print(f"   🎴 卡片数: {len(response.generated_cards)}")
            print(f"   ⏱️ 时间: {response.total_execution_time:.2f}秒")
            
        except Exception as e:
            print(f"   ❌ 失败: {str(e)}")


async def main():
    """主函数 - 运行所有演示"""
    print("🎯 Pipeline模拟用户数据测试演示")
    print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print("\n" + "=" * 60)
    
    try:
        # 运行基础测试
        await test_basic_pipeline()
        
        # 运行用户类型测试
        await test_different_user_types()
        
        # 运行模式测试
        await test_pipeline_modes()
        
        print("\n" + "=" * 60)
        print("🎉 所有演示测试完成!")
        print("💡 提示: 查看控制台输出了解不同用户类型和模式的效果差异")
        
    except Exception as e:
        logger.error(f"演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 