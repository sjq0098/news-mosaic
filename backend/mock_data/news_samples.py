"""
模拟新闻数据 - 用于测试完整的RAG流水线
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

class MockNewsDatabase:
    """模拟新闻数据库"""
    
    def __init__(self):
        self.news_data = self._generate_sample_news()
    
    def _generate_sample_news(self) -> List[Dict[str, Any]]:
        """生成样本新闻数据"""
        base_time = datetime.now()
        
        news_samples = [
            {
                "id": str(uuid.uuid4()),
                "title": "中国AI大模型技术实现重大突破，性能超越GPT-4",
                "content": """
                据科技部最新消息，中国自主研发的AI大模型在多项基准测试中表现优异，在自然语言理解、逻辑推理和代码生成等核心能力上已达到国际先进水平。
                
                这一突破标志着中国在人工智能领域的自主创新能力显著提升。新模型采用了创新的Transformer架构优化和训练策略，在相同参数规模下实现了更高的性能。
                
                专家表示，该技术突破将加速AI在教育、医疗、金融等行业的应用落地，有望推动数字经济高质量发展。同时，这也为中国在全球AI竞争中赢得了重要的话语权。
                """,
                "source": "科技日报",
                "url": "https://example.com/ai-breakthrough-2024",
                "published_at": base_time - timedelta(hours=2),
                "category": "科技",
                "tags": ["AI", "大模型", "科技创新", "数字经济"],
                "sentiment_score": 0.8,
                "sentiment_label": "positive"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "全球半导体供应链面临新挑战，多国加强合作应对",
                "content": """
                国际半导体产业协会发布最新报告显示，全球半导体供应链正面临原材料短缺、地缘政治风险等多重挑战。
                
                报告指出，当前芯片需求持续增长，特别是在AI、新能源汽车、5G通信等领域。然而，供应端却受到多种因素制约，包括制造设备交付延迟、关键材料供应紧张等。
                
                为应对这一挑战，多个国家和地区正在加强国际合作，建立更加稳定和可持续的半导体供应链体系。业内专家认为，这将推动全球半导体产业格局的重新调整。
                """,
                "source": "财经新闻网",
                "url": "https://example.com/semiconductor-supply-chain",
                "published_at": base_time - timedelta(hours=5),
                "category": "财经",
                "tags": ["半导体", "供应链", "国际合作", "芯片"],
                "sentiment_score": -0.2,
                "sentiment_label": "negative"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "新能源汽车销量创历史新高，市场渗透率超过35%",
                "content": """
                中国汽车工业协会发布数据显示，2024年新能源汽车销量同比增长42%，市场渗透率已超过35%，创历史新高。
                
                数据显示，纯电动汽车和插电式混合动力汽车销量均实现大幅增长。其中，比亚迪、特斯拉、理想汽车等品牌表现突出，在技术创新和市场推广方面都有显著进展。
                
                业内分析认为，政策支持、技术进步和消费者接受度提升是推动新能源汽车快速发展的主要因素。预计未来几年，新能源汽车将继续保持高速增长态势。
                """,
                "source": "汽车之家",
                "url": "https://example.com/new-energy-vehicles",
                "published_at": base_time - timedelta(hours=8),
                "category": "汽车",
                "tags": ["新能源汽车", "销量", "市场渗透率", "技术创新"],
                "sentiment_score": 0.7,
                "sentiment_label": "positive"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "量子计算领域获得重要进展，实用化步伐加速",
                "content": """
                清华大学和中科院联合研究团队在量子计算领域取得重要突破，成功构建了具有100个量子比特的超导量子计算系统。
                
                该系统在量子算法演示、量子纠错等关键技术方面都有显著进展。研究团队表示，这一成果将为量子计算的实用化奠定重要基础。
                
                量子计算被认为是下一代计算技术的重要发展方向，在密码学、药物发现、金融建模等领域具有巨大潜力。专家预测，随着技术不断成熟，量子计算将在未来10年内开始进入商业应用阶段。
                """,
                "source": "中国科学报",
                "url": "https://example.com/quantum-computing",
                "published_at": base_time - timedelta(hours=12),
                "category": "科技",
                "tags": ["量子计算", "科研突破", "实用化", "清华大学"],
                "sentiment_score": 0.6,
                "sentiment_label": "positive"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "教育部发布AI教育指导意见，推动智慧教育发展",
                "content": """
                教育部近日发布《关于推进人工智能在教育领域应用的指导意见》，明确了AI教育的发展目标和实施路径。
                
                指导意见提出，要构建智慧教育生态体系，推动AI技术与教育教学深度融合。包括建设智能教学平台、开发个性化学习系统、提升教师数字素养等重点任务。
                
                教育专家表示，AI技术的应用将有助于实现教育资源的优化配置，提高教育质量和效率。同时，也需要关注数据隐私保护和教育公平等问题。
                """,
                "source": "人民日报",
                "url": "https://example.com/ai-education-policy",
                "published_at": base_time - timedelta(hours=18),
                "category": "教育",
                "tags": ["AI教育", "智慧教育", "教育政策", "数字化转型"],
                "sentiment_score": 0.5,
                "sentiment_label": "neutral"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "5G网络建设提速，全国覆盖率达到85%",
                "content": """
                工信部最新统计显示，全国5G基站数量已超过300万个，5G网络覆盖率达到85%，为数字经济发展提供了强有力的基础设施支撑。
                
                5G网络的快速发展推动了工业互联网、智能制造、远程医疗等新兴应用场景的落地。特别是在智慧城市建设、自动驾驶、虚拟现实等领域，5G技术发挥了重要作用。
                
                运营商表示，将继续加大5G网络建设投入，计划在2025年实现全国范围内的5G网络全覆盖。同时，也在积极推进6G技术的研发工作。
                """,
                "source": "通信世界",
                "url": "https://example.com/5g-network-coverage",
                "published_at": base_time - timedelta(days=1),
                "category": "通信",
                "tags": ["5G网络", "数字基础设施", "工业互联网", "智慧城市"],
                "sentiment_score": 0.4,
                "sentiment_label": "neutral"
            }
        ]
        
        return news_samples
    
    def get_all_news(self) -> List[Dict[str, Any]]:
        """获取所有新闻"""
        return self.news_data
    
    def get_news_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取新闻"""
        return [news for news in self.news_data if news["category"] == category]
    
    def get_recent_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的新闻"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [news for news in self.news_data if news["published_at"] > cutoff_time]
    
    def search_news(self, query: str) -> List[Dict[str, Any]]:
        """简单的新闻搜索"""
        query_lower = query.lower()
        results = []
        
        for news in self.news_data:
            # 搜索标题、内容、标签
            if (query_lower in news["title"].lower() or 
                query_lower in news["content"].lower() or
                any(query_lower in tag.lower() for tag in news["tags"])):
                results.append(news)
        
        return results
    
    def get_news_by_id(self, news_id: str) -> Dict[str, Any]:
        """根据ID获取新闻"""
        for news in self.news_data:
            if news["id"] == news_id:
                return news
        return None

# 创建全局实例
mock_news_db = MockNewsDatabase() 