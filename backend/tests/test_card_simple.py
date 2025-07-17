"""
新闻卡片生成功能简化测试
避免复杂依赖，直接测试核心功能
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入需要的模型
from models.news import NewsModel, NewsSource, NewsCategory
from models.news_card import (
    NewsCardRequest, NewsCard, NewsCardMetadata, NewsTheme,
    ImportanceLevel, CredibilityLevel, SentimentLabel, SentimentConfidence
)


class SimpleNewsCardGenerator:
    """简化的新闻卡片生成器"""
    
    async def generate_card_metadata(self, news: NewsModel) -> NewsCardMetadata:
        """生成卡片元数据"""
        
        # 模拟各种分析结果
        metadata = NewsCardMetadata(
            news_id=news.id,
            card_id=f"card_{news.id}_{int(time.time())}",
            
            # 内容分析
            summary=f"这是关于{news.title}的智能摘要。{news.summary[:100] if news.summary else ''}",
            enhanced_summary=f"增强摘要：{news.title}。这条新闻涉及{news.category.value}领域的重要发展。",
            key_points=[
                "核心要点1：主要事件描述",
                "核心要点2：影响分析", 
                "核心要点3：未来趋势"
            ],
            
            # 关键词和主题
            keywords=news.keywords or ["新闻", "分析", news.category.value],
            hashtags=[f"#{keyword}" for keyword in (news.keywords or ["新闻"])[:3]],
            themes=NewsTheme(
                primary_theme=f"{news.category.value}相关新闻",
                secondary_themes=["社会影响", "行业发展"],
                theme_confidence=0.85
            ),
            
            # 情感分析
            sentiment_label=SentimentLabel.NEUTRAL,
            sentiment_score=0.1,
            sentiment_confidence=SentimentConfidence.MEDIUM,
            emotional_keywords=["发展", "进步"],
            
            # 重要性分析
            importance_score=6.5,
            importance_level=ImportanceLevel.MEDIUM,
            importance_reasons=["行业相关", "公众关注", "影响范围较广"],
            
            # 可信度分析
            credibility_score=7.0,
            credibility_level=CredibilityLevel.RELIABLE,
            credibility_factors=["来源可靠", "信息完整", "逻辑清晰"],
            
            # 实体识别
            entities=[],
            people=[],
            organizations=[],
            locations=[],
            
            # 时效性
            urgency_score=5.0,
            freshness_score=8.0,
            time_sensitivity=False,
            
            # 推荐信息
            target_audience=["一般读者", "行业从业者"],
            reading_time_minutes=3,
            difficulty_level="medium",
            
            # 相关性
            related_news_ids=[],
            similarity_scores={},
            
            # 生成信息
            generation_model="qwen-test",
            generation_time=0.5
        )
        
        return metadata
    
    async def generate_card(self, news: NewsModel) -> NewsCard:
        """生成完整新闻卡片"""
        metadata = await self.generate_card_metadata(news)
        
        card = NewsCard(
            news_id=news.id,
            title=news.title,
            url=str(news.url),
            image_url=str(news.image_url) if news.image_url else None,
            source=news.source,
            category=news.category,
            published_at=news.published_at,
            metadata=metadata,
            is_featured=metadata.importance_score >= 8.0,
            display_priority=int(metadata.importance_score)
        )
        
        return card


def create_sample_news() -> List[NewsModel]:
    """创建示例新闻数据"""
    return [
        NewsModel(
            id="news_001",
            title="人工智能技术取得重大突破，新型AI芯片性能提升300%",
            summary="近日，某科技公司发布了新一代AI芯片，在深度学习推理速度上较前代产品提升300%，能耗降低50%。",
            content="这是一条关于AI技术突破的详细新闻内容...",
            url="https://example.com/news/ai-chip-breakthrough",
            image_url="https://example.com/images/ai-chip.jpg",
            source=NewsSource.MANUAL,
            publisher="科技日报",
            category=NewsCategory.TECHNOLOGY,
            keywords=["人工智能", "AI芯片", "深度学习", "科技突破"],
            published_at=datetime.utcnow(),
            view_count=15432,
            like_count=892,
            share_count=234
        ),
        NewsModel(
            id="news_002",
            title="全球气候变化加剧，极端天气事件频发引发担忧", 
            summary="联合国最新报告显示，过去一年全球极端天气事件较往年增加40%，气候变化对全球生态系统和人类社会带来严重威胁。",
            content="这是一条关于气候变化的详细新闻内容...",
            url="https://example.com/news/climate-change-warning",
            image_url="https://example.com/images/climate.jpg",
            source=NewsSource.RSS,
            publisher="环球时报",
            category=NewsCategory.SCIENCE,
            keywords=["气候变化", "极端天气", "全球变暖", "环境保护"],
            published_at=datetime.utcnow(),
            view_count=23456,
            like_count=1234,
            share_count=567
        )
    ]


async def test_simple_card_generation():
    """测试简化的卡片生成功能"""
    print("=" * 60)
    print("🚀 开始测试新闻结构化卡片生成功能 (简化版)")
    print("=" * 60)
    
    # 创建生成器和示例数据
    generator = SimpleNewsCardGenerator()
    news_list = create_sample_news()
    
    for i, news in enumerate(news_list, 1):
        print(f"\n📋 测试 {i}: 生成新闻卡片")
        print("-" * 40)
        print(f"📰 新闻标题: {news.title}")
        
        try:
            start_time = time.time()
            card = await generator.generate_card(news)
            end_time = time.time()
            
            print(f"✅ 卡片生成成功！")
            print(f"⏱️  处理时间: {end_time - start_time:.3f}秒")
            print(f"🏷️  新闻分类: {card.category}")
            print(f"📊 重要性分数: {card.metadata.importance_score}")
            print(f"📊 重要性级别: {card.metadata.importance_level}")
            print(f"🎭 情感标签: {card.metadata.sentiment_label}")
            print(f"📝 智能摘要: {card.metadata.summary}")
            print(f"🔑 关键词: {', '.join(card.metadata.keywords)}")
            print(f"🏷️  推荐标签: {', '.join(card.metadata.hashtags)}")
            print(f"👥 目标受众: {', '.join(card.metadata.target_audience)}")
            print(f"⏰ 阅读时长: {card.metadata.reading_time_minutes}分钟")
            print(f"🌟 是否特色: {card.is_featured}")
            print(f"📈 显示优先级: {card.display_priority}")
            
            # 显示核心要点
            print(f"🎯 核心要点:")
            for j, point in enumerate(card.metadata.key_points, 1):
                print(f"   {j}. {point}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("🎉 新闻卡片生成功能测试完成！")
    print("=" * 60)
    
    return True


def display_card_structure():
    """显示卡片数据结构"""
    print("\n📄 新闻卡片JSON结构说明:")
    print("-" * 40)
    
    structure = {
        "news_id": "新闻唯一标识",
        "title": "新闻标题", 
        "url": "新闻链接",
        "image_url": "新闻图片",
        "source": "新闻来源",
        "category": "新闻分类",
        "published_at": "发布时间",
        "metadata": {
            "summary": "智能摘要",
            "enhanced_summary": "增强摘要",
            "key_points": ["核心要点列表"],
            "keywords": ["关键词列表"],
            "hashtags": ["推荐标签"],
            "themes": {
                "primary_theme": "主要主题",
                "secondary_themes": ["次要主题"],
                "theme_confidence": "主题置信度"
            },
            "sentiment": {
                "label": "情感标签",
                "score": "情感分数",
                "confidence": "置信度"
            },
            "importance": {
                "score": "重要性分数",
                "level": "重要性级别", 
                "reasons": ["重要性原因"]
            },
            "credibility": {
                "score": "可信度分数",
                "level": "可信度级别",
                "factors": ["可信度因素"]
            },
            "target_audience": ["目标受众"],
            "reading_time_minutes": "预估阅读时长",
            "difficulty_level": "阅读难度"
        },
        "is_featured": "是否为特色新闻",
        "display_priority": "显示优先级"
    }
    
    print(json.dumps(structure, ensure_ascii=False, indent=2))


async def main():
    """主函数"""
    success = await test_simple_card_generation()
    
    if success:
        display_card_structure()
        
        print("\n🚀 实际使用方式:")
        print("1. 通过API调用: POST /api/v1/news-cards/generate")
        print("2. 传入NewsCardRequest参数")
        print("3. 获得NewsCardResponse结果")
        
        print("\n📝 前端集成建议:")
        print("1. 根据重要性级别设置卡片样式")
        print("2. 使用情感标签显示情感图标")
        print("3. 关键词可作为可点击标签")
        print("4. 根据目标受众推荐给特定用户")
        print("5. 使用阅读时长帮助用户规划时间")


if __name__ == "__main__":
    asyncio.run(main()) 