"""
新闻卡片生成功能测试
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.news import NewsModel, NewsSource, NewsCategory
from models.news_card import NewsCardRequest, NewsCard
from services.news_card_service import NewsCardService


class MockNewsData:
    """模拟新闻数据"""
    
    @staticmethod
    def get_sample_news() -> List[Dict[str, Any]]:
        """获取样本新闻数据"""
        return [
            {
                "id": "news_001",
                "title": "人工智能技术取得重大突破，新型AI芯片性能提升300%",
                "summary": "近日，某科技公司发布了新一代AI芯片，在深度学习推理速度上较前代产品提升300%，能耗降低50%。这一突破将推动AI技术在各行业的广泛应用。",
                "content": """
                近日，全球领先的科技公司XYZ Corp发布了其最新研发的第四代AI芯片"智慧芯X4"。据官方数据显示，该芯片在深度学习推理速度上较前代产品提升了300%，同时能耗降低了50%，标志着AI芯片技术的重大突破。

                该芯片采用了全新的神经网络架构优化技术，支持多种主流深度学习框架，包括TensorFlow、PyTorch和PaddlePaddle等。在实际测试中，该芯片在图像识别、自然语言处理和语音识别等任务上均表现出色。

                XYZ Corp首席技术官表示："这一突破不仅提升了AI计算的效率，更重要的是降低了AI技术的应用门槛，将推动人工智能在自动驾驶、智慧城市、医疗诊断等领域的广泛应用。"

                业界专家认为，这一技术突破将进一步加速AI产业的发展，预计未来五年内，AI芯片市场规模将增长至千亿美元级别。
                """,
                "url": "https://example.com/news/ai-chip-breakthrough",
                "image_url": "https://example.com/images/ai-chip.jpg",
                "source": NewsSource.MANUAL,
                "publisher": "科技日报",
                "category": NewsCategory.TECHNOLOGY,
                "keywords": ["人工智能", "AI芯片", "深度学习", "科技突破"],
                "published_at": datetime.utcnow(),
                "view_count": 15432,
                "like_count": 892,
                "share_count": 234
            },
            {
                "id": "news_002", 
                "title": "全球气候变化加剧，极端天气事件频发引发担忧",
                "summary": "联合国最新报告显示，过去一年全球极端天气事件较往年增加40%，气候变化对全球生态系统和人类社会带来严重威胁。",
                "content": """
                联合国环境规划署发布的最新报告显示，过去一年全球极端天气事件较往年增加了40%，包括超强台风、长期干旱、洪涝灾害和异常高温等。气候科学家警告，这一趋势表明全球气候变化正在加速。

                报告指出，北极地区冰川融化速度比预期快30%，海平面上升速度也在加快。同时，全球平均气温已连续三年刷新历史记录，比工业革命前水平高出1.2摄氏度。

                联合国秘书长在报告发布会上表示："我们正面临气候紧急状态，必须立即采取行动减少温室气体排放，否则将面临不可逆转的环境灾难。"

                专家建议，各国应加快能源转型，大力发展可再生能源，同时加强国际合作应对气候变化挑战。
                """,
                "url": "https://example.com/news/climate-change-warning",
                "image_url": "https://example.com/images/climate.jpg",
                "source": NewsSource.RSS,
                "publisher": "环球时报",
                "category": NewsCategory.SCIENCE,
                "keywords": ["气候变化", "极端天气", "全球变暖", "环境保护"],
                "published_at": datetime.utcnow(),
                "view_count": 23456,
                "like_count": 1234,
                "share_count": 567
            },
            {
                "id": "news_003",
                "title": "中国经济稳步复苏，第三季度GDP同比增长6.8%",
                "summary": "国家统计局发布数据显示，第三季度GDP同比增长6.8%，经济运行总体平稳，新兴产业发展迅速，为全年经济目标实现奠定基础。",
                "content": """
                国家统计局今日发布第三季度经济数据，GDP同比增长6.8%，环比增长1.2%，显示中国经济继续保持稳步复苏态势。

                数据显示，工业生产稳定增长，高技术制造业增加值同比增长12.3%，新能源汽车、集成电路、工业机器人等新兴产业表现亮眼。服务业也呈现良好发展势头，信息技术服务、科学研究和技术服务等现代服务业增长较快。

                消费市场持续恢复，社会消费品零售总额同比增长4.6%，网上零售额增长更是达到11.2%。投资结构不断优化，制造业投资和基础设施投资保持较快增长。

                专家分析认为，中国经济展现出较强的韧性和活力，新动能持续增强，为完成全年经济社会发展目标提供了有力支撑。
                """,
                "url": "https://example.com/news/china-economy-q3",
                "image_url": "https://example.com/images/economy.jpg",
                "source": NewsSource.BING,
                "publisher": "人民日报",
                "category": NewsCategory.BUSINESS,
                "keywords": ["中国经济", "GDP增长", "经济复苏", "统计数据"],
                "published_at": datetime.utcnow(),
                "view_count": 34567,
                "like_count": 2345,
                "share_count": 789
            }
        ]


class MockNewsService:
    """模拟新闻服务"""
    
    def __init__(self):
        self.news_data = {
            news["id"]: NewsModel(**news) 
            for news in MockNewsData.get_sample_news()
        }
    
    async def get_news_by_id(self, news_id: str) -> NewsModel:
        """根据ID获取新闻"""
        if news_id not in self.news_data:
            return None
        return self.news_data[news_id]


class MockQWENService:
    """模拟QWen服务"""
    
    async def chat(self, prompt: str) -> object:
        """模拟聊天响应"""
        # 根据不同的prompt返回不同的模拟响应
        if "结构化分析" in prompt or "摘要" in prompt:
            response_content = json.dumps({
                "summary": "这是一条关于AI技术突破的重要新闻，展示了科技发展的最新成果。",
                "enhanced_summary": "人工智能芯片技术取得重大突破，新型AI芯片性能大幅提升，标志着AI技术发展进入新阶段。这一突破将推动AI在各行业的广泛应用，加速数字化转型进程。",
                "key_points": [
                    "AI芯片性能提升300%",
                    "能耗降低50%",
                    "支持多种深度学习框架",
                    "将推动AI广泛应用",
                    "预计市场规模达千亿美元"
                ],
                "keywords": ["人工智能", "AI芯片", "深度学习", "技术突破", "性能提升"],
                "hashtags": ["#人工智能", "#AI芯片", "#科技突破", "#深度学习", "#未来科技"]
            }, ensure_ascii=False)
        elif "情感分析" in prompt:
            response_content = json.dumps({
                "label": "positive",
                "score": 0.8,
                "confidence": "high",
                "keywords": ["突破", "提升", "推动", "发展"],
                "reasons": ["技术进步带来积极影响", "性能大幅提升", "市场前景良好"]
            }, ensure_ascii=False)
        elif "主题分析" in prompt:
            response_content = json.dumps({
                "primary_theme": "人工智能技术突破",
                "secondary_themes": ["芯片技术", "深度学习", "产业发展"],
                "theme_confidence": 0.92
            }, ensure_ascii=False)
        elif "重要性" in prompt:
            response_content = json.dumps({
                "score": 8.5,
                "level": "high",
                "reasons": ["技术突破具有重大意义", "影响多个行业发展", "市场关注度高"]
            }, ensure_ascii=False)
        elif "可信度" in prompt:
            response_content = json.dumps({
                "score": 8.0,
                "level": "reliable",
                "factors": ["官方发布", "权威媒体报道", "技术数据详实", "专家认可"]
            }, ensure_ascii=False)
        elif "实体识别" in prompt:
            response_content = json.dumps({
                "entities": [
                    {"entity": "XYZ Corp", "entity_type": "organization", "mention_count": 2, "confidence": 0.95},
                    {"entity": "智慧芯X4", "entity_type": "product", "mention_count": 1, "confidence": 0.9},
                    {"entity": "TensorFlow", "entity_type": "technology", "mention_count": 1, "confidence": 0.85}
                ],
                "people": ["首席技术官"],
                "organizations": ["XYZ Corp", "联合国环境规划署"],
                "locations": ["全球", "北极地区"]
            }, ensure_ascii=False)
        else:
            response_content = json.dumps({
                "result": "模拟响应",
                "status": "success"
            }, ensure_ascii=False)
        
        # 创建模拟响应对象
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse(response_content)


class MockVectorDBService:
    """模拟向量数据库服务"""
    
    async def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """模拟相似搜索"""
        # 返回模拟的相关新闻
        return [
            {"news_id": "news_002", "score": 0.75},
            {"news_id": "news_003", "score": 0.68}
        ]


async def test_news_card_generation():
    """测试新闻卡片生成功能"""
    print("=" * 60)
    print("🚀 开始测试新闻结构化卡片生成功能")
    print("=" * 60)
    
    # 创建服务实例（注入模拟依赖）
    card_service = NewsCardService()
    card_service.news_service = MockNewsService()
    card_service.qwen_service = MockQWENService()
    card_service.vector_service = MockVectorDBService()
    
    # 测试用例1：生成基础卡片
    print("\n📋 测试1: 生成基础新闻卡片")
    print("-" * 40)
    
    request = NewsCardRequest(
        news_id="news_001",
        include_sentiment=True,
        include_entities=True,
        include_related=True,
        max_summary_length=300
    )
    
    try:
        start_time = time.time()
        response = await card_service.generate_card(request)
        end_time = time.time()
        
        print(f"✅ 卡片生成成功！")
        print(f"⏱️  处理时间: {end_time - start_time:.2f}秒")
        print(f"📰 新闻标题: {response.card.title}")
        print(f"🏷️  新闻分类: {response.card.category}")
        print(f"📊 重要性分数: {response.card.metadata.importance_score}")
        print(f"🎭 情感标签: {response.card.metadata.sentiment_label}")
        print(f"📝 智能摘要: {response.card.metadata.summary[:100]}...")
        print(f"🔑 关键词数量: {len(response.card.metadata.keywords)}")
        print(f"👥 实体数量: {len(response.card.metadata.entities)}")
        print(f"🔗 相关新闻: {len(response.card.metadata.related_news_ids)}")
        
        if response.warnings:
            print(f"⚠️  警告信息: {response.warnings}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 测试用例2：批量生成卡片
    print("\n📋 测试2: 批量生成新闻卡片")
    print("-" * 40)
    
    from models.news_card import BatchNewsCardRequest
    
    batch_request = BatchNewsCardRequest(
        news_ids=["news_001", "news_002", "news_003"],
        include_sentiment=True,
        include_entities=True,
        include_related=False,  # 减少处理时间
        max_summary_length=200
    )
    
    try:
        start_time = time.time()
        batch_response = await card_service.generate_batch_cards(batch_request)
        end_time = time.time()
        
        print(f"✅ 批量生成成功！")
        print(f"⏱️  总处理时间: {end_time - start_time:.2f}秒")
        print(f"📊 总数量: {batch_response.total_count}")
        print(f"✅ 成功数量: {batch_response.success_count}")
        print(f"❌ 失败数量: {batch_response.failed_count}")
        
        # 显示每个卡片的基本信息
        for i, card in enumerate(batch_response.cards, 1):
            print(f"\n📰 卡片 {i}:")
            print(f"   标题: {card.title[:50]}...")
            print(f"   重要性: {card.metadata.importance_level} ({card.metadata.importance_score})")
            print(f"   情感: {card.metadata.sentiment_label} ({card.metadata.sentiment_score:.2f})")
            print(f"   是否特色: {card.is_featured}")
        
    except Exception as e:
        print(f"❌ 批量测试失败: {e}")
        return False
    
    # 测试用例3：不同模板生成
    print("\n📋 测试3: 使用不同模板生成卡片")
    print("-" * 40)
    
    templates = {
        "fast": {"include_sentiment": False, "include_entities": False, "include_related": False, "max_summary_length": 150},
        "basic": {"include_sentiment": True, "include_entities": False, "include_related": False, "max_summary_length": 200},
        "comprehensive": {"include_sentiment": True, "include_entities": True, "include_related": True, "max_summary_length": 400}
    }
    
    for template_name, template_config in templates.items():
        print(f"\n🎨 测试模板: {template_name}")
        
        template_request = NewsCardRequest(
            news_id="news_002",
            **template_config
        )
        
        try:
            start_time = time.time()
            template_response = await card_service.generate_card(template_request)
            end_time = time.time()
            
            print(f"   ✅ 生成成功 ({end_time - start_time:.2f}s)")
            print(f"   📝 摘要长度: {len(template_response.card.metadata.summary)}")
            print(f"   🎭 包含情感分析: {template_config['include_sentiment']}")
            print(f"   👥 包含实体识别: {template_config['include_entities']}")
            print(f"   🔗 包含相关新闻: {template_config['include_related']}")
            
        except Exception as e:
            print(f"   ❌ 模板测试失败: {e}")
    
    # 测试用例4：测试错误处理
    print("\n📋 测试4: 错误处理测试")
    print("-" * 40)
    
    # 测试不存在的新闻ID
    try:
        error_request = NewsCardRequest(news_id="non_existent_news")
        await card_service.generate_card(error_request)
        print("❌ 错误：应该抛出异常但没有")
    except Exception as e:
        print(f"✅ 正确处理错误: {type(e).__name__}")
    
    print("\n" + "=" * 60)
    print("🎉 新闻卡片生成功能测试完成！")
    print("=" * 60)
    
    return True


def display_card_json_example(card: NewsCard):
    """显示卡片JSON示例"""
    print("\n📄 生成的卡片JSON结构示例:")
    print("-" * 40)
    
    # 简化的卡片数据用于展示
    simplified_card = {
        "news_id": card.news_id,
        "title": card.title,
        "metadata": {
            "summary": card.metadata.summary,
            "key_points": card.metadata.key_points[:3],  # 只显示前3个要点
            "keywords": card.metadata.keywords[:5],      # 只显示前5个关键词
            "sentiment": {
                "label": card.metadata.sentiment_label,
                "score": card.metadata.sentiment_score,
                "confidence": card.metadata.sentiment_confidence
            },
            "importance": {
                "score": card.metadata.importance_score,
                "level": card.metadata.importance_level
            },
            "reading_time_minutes": card.metadata.reading_time_minutes,
            "target_audience": card.metadata.target_audience
        },
        "is_featured": card.is_featured,
        "display_priority": card.display_priority
    }
    
    print(json.dumps(simplified_card, ensure_ascii=False, indent=2))


async def main():
    """主函数"""
    success = await test_news_card_generation()
    
    if success:
        print("\n🚀 可以通过以下API端点测试:")
        print("POST /api/v1/news-cards/generate")
        print("POST /api/v1/news-cards/generate/batch")
        print("GET  /api/v1/news-cards/quick-generate/{news_id}")
        print("GET  /api/v1/news-cards/templates")
        print("POST /api/v1/news-cards/templates/{template_name}/generate/{news_id}")
        
        print("\n📝 前端开发提示:")
        print("1. 卡片可以根据重要性级别设置不同颜色")
        print("2. 情感分析结果可以用表情符号显示")
        print("3. 关键词可以作为标签云展示")
        print("4. 相关新闻可以作为推荐链接")
        print("5. 实体可以支持点击查看详情")


if __name__ == "__main__":
    asyncio.run(main()) 