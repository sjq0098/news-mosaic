"""
新闻结构化卡片生成服务
"""

import asyncio
import json
import time
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger

from services.qwen_service import QWENService
from services.news_service import NewsService
from services.vector_db_service import get_vector_db
from models.news_card import (
    NewsCard, NewsCardMetadata, NewsTheme, EntityMention,
    ImportanceLevel, CredibilityLevel, SentimentLabel, SentimentConfidence,
    NewsCardRequest, NewsCardResponse, BatchNewsCardRequest, BatchNewsCardResponse
)
from models.news import NewsModel
from models.sentiment import SentimentAnalysisRequest
from core.config import settings


class NewsCardService:
    """新闻结构化卡片生成服务"""
    
    def __init__(self):
        self.qwen_service = QWENService()
        self.news_service = NewsService()
        self.vector_service = get_vector_db()
        
    async def generate_card(self, request: NewsCardRequest) -> NewsCardResponse:
        """生成单个新闻卡片"""
        start_time = time.time()
        warnings = []
        
        try:
            # 获取新闻数据
            news = await self.news_service.get_news_by_id(request.news_id)
            if not news:
                raise ValueError(f"新闻 {request.news_id} 不存在")
            
            # 并行执行各种分析
            tasks = []
            
            # 1. 生成摘要和关键点
            tasks.append(self._generate_summary_and_keypoints(news, request.max_summary_length))
            
            # 2. 情感分析
            if request.include_sentiment:
                tasks.append(self._analyze_sentiment(news))
            else:
                tasks.append(asyncio.create_task(self._default_sentiment()))
            
            # 3. 主题分析
            tasks.append(self._analyze_themes(news))
            
            # 4. 重要性分析
            tasks.append(self._analyze_importance(news))
            
            # 5. 可信度分析
            tasks.append(self._analyze_credibility(news))
            
            # 6. 实体识别
            if request.include_entities:
                tasks.append(self._extract_entities(news))
            else:
                tasks.append(asyncio.create_task(self._default_entities()))
            
            # 7. 时效性分析
            tasks.append(self._analyze_timeliness(news))
            
            # 执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            summary_data = results[0] if not isinstance(results[0], Exception) else {}
            sentiment_data = results[1] if not isinstance(results[1], Exception) else {}
            theme_data = results[2] if not isinstance(results[2], Exception) else {}
            importance_data = results[3] if not isinstance(results[3], Exception) else {}
            credibility_data = results[4] if not isinstance(results[4], Exception) else {}
            entity_data = results[5] if not isinstance(results[5], Exception) else {}
            timeliness_data = results[6] if not isinstance(results[6], Exception) else {}
            
            # 查找相关新闻
            related_news_ids = []
            similarity_scores = {}
            if request.include_related:
                try:
                    related_results = await self._find_related_news(news)
                    related_news_ids = related_results.get('news_ids', [])
                    similarity_scores = related_results.get('similarity_scores', {})
                except Exception as e:
                    logger.warning(f"查找相关新闻失败: {e}")
                    warnings.append("相关新闻查找失败")
            
            # 生成推荐信息
            recommendation_data = await self._generate_recommendations(news, summary_data)
            
            # 构建卡片元数据
            metadata = NewsCardMetadata(
                news_id=news.id,
                card_id=f"card_{news.id}_{int(time.time())}",
                
                # 内容分析
                summary=summary_data.get('summary', ''),
                enhanced_summary=summary_data.get('enhanced_summary', ''),
                key_points=summary_data.get('key_points', []),
                
                # 关键词和主题
                keywords=summary_data.get('keywords', []),
                hashtags=summary_data.get('hashtags', []),
                themes=NewsTheme(
                    primary_theme=theme_data.get('primary_theme', '其他'),
                    secondary_themes=theme_data.get('secondary_themes', []),
                    theme_confidence=theme_data.get('theme_confidence', 0.5)
                ),
                
                # 情感分析
                sentiment_label=sentiment_data.get('label', SentimentLabel.NEUTRAL),
                sentiment_score=sentiment_data.get('score', 0.0),
                sentiment_confidence=sentiment_data.get('confidence', SentimentConfidence.MEDIUM),
                emotional_keywords=sentiment_data.get('keywords', []),
                
                # 重要性分析
                importance_score=importance_data.get('score', 5.0),
                importance_level=importance_data.get('level', ImportanceLevel.MEDIUM),
                importance_reasons=importance_data.get('reasons', []),
                
                # 可信度分析
                credibility_score=credibility_data.get('score', 5.0),
                credibility_level=credibility_data.get('level', CredibilityLevel.MODERATE),
                credibility_factors=credibility_data.get('factors', []),
                
                # 实体识别
                entities=entity_data.get('entities', []),
                people=entity_data.get('people', []),
                organizations=entity_data.get('organizations', []),
                locations=entity_data.get('locations', []),
                
                # 时效性
                urgency_score=timeliness_data.get('urgency_score', 5.0),
                freshness_score=timeliness_data.get('freshness_score', 5.0),
                time_sensitivity=timeliness_data.get('time_sensitivity', False),
                
                # 推荐信息
                target_audience=recommendation_data.get('target_audience', []),
                reading_time_minutes=recommendation_data.get('reading_time', 5),
                difficulty_level=recommendation_data.get('difficulty_level', 'medium'),
                
                # 相关性
                related_news_ids=related_news_ids,
                similarity_scores=similarity_scores,
                
                # 生成信息
                generation_model=request.generation_model or settings.QWEN_MODEL,
                generation_time=time.time() - start_time
            )
            
            # 构建完整卡片
            card = NewsCard(
                news_id=news.id,
                title=news.title,
                url=str(news.url),
                image_url=str(news.image_url) if news.image_url else None,
                source=news.source,
                category=news.category,
                published_at=news.published_at,
                metadata=metadata,
                is_featured=importance_data.get('score', 5.0) >= 8.0,
                display_priority=int(importance_data.get('score', 5.0))
            )
            
            processing_time = time.time() - start_time
            logger.info(f"新闻卡片生成完成: {news.id}, 耗时: {processing_time:.2f}s")
            
            return NewsCardResponse(
                card=card,
                processing_time=processing_time,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"生成新闻卡片失败: {e}")
            raise
    
    async def generate_batch_cards(self, request: BatchNewsCardRequest) -> BatchNewsCardResponse:
        """批量生成新闻卡片"""
        start_time = time.time()
        cards = []
        failed_news_ids = []
        
        # 并行处理多个新闻
        tasks = []
        for news_id in request.news_ids:
            card_request = NewsCardRequest(
                news_id=news_id,
                include_sentiment=request.include_sentiment,
                include_entities=request.include_entities,
                include_related=request.include_related,
                max_summary_length=request.max_summary_length,
                generation_model=request.generation_model
            )
            tasks.append(self.generate_card(card_request))
        
        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"生成卡片失败 {request.news_ids[i]}: {result}")
                failed_news_ids.append(request.news_ids[i])
            else:
                cards.append(result.card)
        
        processing_time = time.time() - start_time
        
        return BatchNewsCardResponse(
            cards=cards,
            total_count=len(request.news_ids),
            success_count=len(cards),
            failed_count=len(failed_news_ids),
            processing_time=processing_time,
            failed_news_ids=failed_news_ids
        )
    
    async def _generate_summary_and_keypoints(self, news: NewsModel, max_length: int) -> Dict[str, Any]:
        """生成摘要和关键点"""
        content = news.content or news.summary or news.title
        
        prompt = f"""
请对以下新闻内容进行结构化分析，生成JSON格式的结果：

新闻标题：{news.title}
新闻内容：{content[:2000]}  # 限制长度避免太长

请分析并返回JSON格式的结果，包含以下字段：
1. summary: 智能摘要（不超过{max_length}字符）
2. enhanced_summary: 增强摘要，包含背景信息（不超过{max_length * 2}字符）
3. key_points: 核心要点列表（最多5个要点）
4. keywords: 关键词列表（最多10个）
5. hashtags: 推荐标签（最多5个，以#开头）

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            # 验证和清理结果
            return {
                'summary': result.get('summary', '')[:max_length],
                'enhanced_summary': result.get('enhanced_summary', '')[:max_length * 2],
                'key_points': result.get('key_points', [])[:5],
                'keywords': result.get('keywords', [])[:10],
                'hashtags': [tag if tag.startswith('#') else f"#{tag}" for tag in result.get('hashtags', [])][:5]
            }
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return {
                'summary': news.summary or news.title[:max_length],
                'enhanced_summary': news.summary or news.title,
                'key_points': [news.title],
                'keywords': [],
                'hashtags': []
            }
    
    async def _analyze_sentiment(self, news: NewsModel) -> Dict[str, Any]:
        """分析情感"""
        content = news.content or news.summary or news.title
        
        prompt = f"""
请对以下新闻内容进行情感分析，返回JSON格式：

新闻内容：{content[:1000]}

请分析并返回JSON格式的结果，包含以下字段：
1. label: 情感标签（positive/negative/neutral/mixed）
2. score: 情感分数（-1.0到1.0，负数表示负面，正数表示正面）
3. confidence: 置信度（low/medium/high）
4. keywords: 影响情感判断的关键词列表（最多5个）
5. reasons: 情感判断原因（最多3个）

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            # 映射和验证结果
            label_map = {
                'positive': SentimentLabel.POSITIVE,
                'negative': SentimentLabel.NEGATIVE,
                'neutral': SentimentLabel.NEUTRAL,
                'mixed': SentimentLabel.MIXED
            }
            
            confidence_map = {
                'low': SentimentConfidence.LOW,
                'medium': SentimentConfidence.MEDIUM,
                'high': SentimentConfidence.HIGH
            }
            
            return {
                'label': label_map.get(result.get('label', 'neutral'), SentimentLabel.NEUTRAL),
                'score': max(-1.0, min(1.0, float(result.get('score', 0.0)))),
                'confidence': confidence_map.get(result.get('confidence', 'medium'), SentimentConfidence.MEDIUM),
                'keywords': result.get('keywords', [])[:5],
                'reasons': result.get('reasons', [])[:3]
            }
        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return await self._default_sentiment()
    
    async def _analyze_themes(self, news: NewsModel) -> Dict[str, Any]:
        """分析主题"""
        content = news.content or news.summary or news.title
        
        prompt = f"""
请对以下新闻内容进行主题分析，返回JSON格式：

新闻标题：{news.title}
新闻内容：{content[:1000]}
新闻分类：{news.category}

请分析并返回JSON格式的结果，包含以下字段：
1. primary_theme: 主要主题（一个清晰的主题描述）
2. secondary_themes: 次要主题列表（最多3个）
3. theme_confidence: 主题识别的置信度（0.0-1.0）

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            return {
                'primary_theme': result.get('primary_theme', '一般新闻'),
                'secondary_themes': result.get('secondary_themes', [])[:3],
                'theme_confidence': max(0.0, min(1.0, float(result.get('theme_confidence', 0.5))))
            }
        except Exception as e:
            logger.error(f"主题分析失败: {e}")
            return {
                'primary_theme': str(news.category.value),
                'secondary_themes': [],
                'theme_confidence': 0.5
            }
    
    async def _analyze_importance(self, news: NewsModel) -> Dict[str, Any]:
        """分析重要性"""
        content = news.content or news.summary or news.title
        
        prompt = f"""
请对以下新闻的重要性进行评估，返回JSON格式：

新闻标题：{news.title}
新闻内容：{content[:1000]}
发布时间：{news.published_at}
新闻来源：{news.source}
新闻分类：{news.category}

请根据以下标准评估重要性（0-10分）：
- 影响范围（个人/地区/国家/全球）
- 时效性（是否为突发新闻）
- 公众关注度
- 潜在影响
- 权威性

请分析并返回JSON格式的结果，包含以下字段：
1. score: 重要性分数（0.0-10.0）
2. level: 重要性级别（critical/high/medium/low/minimal）
3. reasons: 重要性判断原因（最多3个）

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            score = max(0.0, min(10.0, float(result.get('score', 5.0))))
            
            # 根据分数确定级别
            if score >= 9.0:
                level = ImportanceLevel.CRITICAL
            elif score >= 7.0:
                level = ImportanceLevel.HIGH
            elif score >= 5.0:
                level = ImportanceLevel.MEDIUM
            elif score >= 3.0:
                level = ImportanceLevel.LOW
            else:
                level = ImportanceLevel.MINIMAL
            
            return {
                'score': score,
                'level': level,
                'reasons': result.get('reasons', [])[:3]
            }
        except Exception as e:
            logger.error(f"重要性分析失败: {e}")
            return {
                'score': 5.0,
                'level': ImportanceLevel.MEDIUM,
                'reasons': ['常规新闻']
            }
    
    async def _analyze_credibility(self, news: NewsModel) -> Dict[str, Any]:
        """分析可信度"""
        
        prompt = f"""
请对以下新闻的可信度进行评估，返回JSON格式：

新闻标题：{news.title}
新闻来源：{news.source}
发布者：{news.publisher or '未知'}
新闻链接：{news.url}

请根据以下标准评估可信度（0-10分）：
- 来源权威性
- 信息完整性
- 是否有明确的发布者
- 链接的可靠性
- 内容的逻辑性

请分析并返回JSON格式的结果，包含以下字段：
1. score: 可信度分数（0.0-10.0）
2. level: 可信度级别（verified/reliable/moderate/questionable/unverified）
3. factors: 影响可信度的因素（最多5个）

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            score = max(0.0, min(10.0, float(result.get('score', 5.0))))
            
            # 根据分数确定级别
            if score >= 9.0:
                level = CredibilityLevel.VERIFIED
            elif score >= 7.0:
                level = CredibilityLevel.RELIABLE
            elif score >= 5.0:
                level = CredibilityLevel.MODERATE
            elif score >= 3.0:
                level = CredibilityLevel.QUESTIONABLE
            else:
                level = CredibilityLevel.UNVERIFIED
            
            return {
                'score': score,
                'level': level,
                'factors': result.get('factors', [])[:5]
            }
        except Exception as e:
            logger.error(f"可信度分析失败: {e}")
            return {
                'score': 5.0,
                'level': CredibilityLevel.MODERATE,
                'factors': ['需要进一步验证']
            }
    
    async def _extract_entities(self, news: NewsModel) -> Dict[str, Any]:
        """提取实体"""
        content = news.content or news.summary or news.title
        
        prompt = f"""
请对以下新闻内容进行实体识别，返回JSON格式：

新闻标题：{news.title}
新闻内容：{content[:1000]}

请识别并返回JSON格式的结果，包含以下字段：
1. entities: 实体列表，每个实体包含：
   - entity: 实体名称
   - entity_type: 实体类型（person/organization/location/other）
   - mention_count: 提及次数
   - confidence: 识别置信度（0.0-1.0）
2. people: 人物名称列表
3. organizations: 机构名称列表
4. locations: 地点名称列表

请确保返回的是有效的JSON格式。
"""
        
        try:
            response = await self.qwen_service.chat(prompt)
            result = self._parse_json_response(response.content)
            
            # 处理实体数据
            entities = []
            for entity_data in result.get('entities', []):
                entity = EntityMention(
                    entity=entity_data.get('entity', ''),
                    entity_type=entity_data.get('entity_type', 'other'),
                    mention_count=int(entity_data.get('mention_count', 1)),
                    confidence=max(0.0, min(1.0, float(entity_data.get('confidence', 0.5))))
                )
                entities.append(entity)
            
            return {
                'entities': entities[:20],  # 限制数量
                'people': result.get('people', [])[:10],
                'organizations': result.get('organizations', [])[:10],
                'locations': result.get('locations', [])[:10]
            }
        except Exception as e:
            logger.error(f"实体识别失败: {e}")
            return await self._default_entities()
    
    async def _analyze_timeliness(self, news: NewsModel) -> Dict[str, Any]:
        """分析时效性"""
        now = datetime.utcnow()
        published_time = news.published_at
        time_diff = now - published_time
        
        # 计算新鲜度分数（基于发布时间）
        hours_old = time_diff.total_seconds() / 3600
        if hours_old < 1:
            freshness_score = 10.0
        elif hours_old < 6:
            freshness_score = 9.0
        elif hours_old < 24:
            freshness_score = 8.0
        elif hours_old < 72:
            freshness_score = 6.0
        elif hours_old < 168:  # 1周
            freshness_score = 4.0
        else:
            freshness_score = 2.0
        
        # 基于内容分析紧急程度
        content = news.content or news.summary or news.title
        urgent_keywords = ['突发', '紧急', '重大', '立即', '警报', '事故', '灾害', '袭击', '爆炸']
        urgency_score = 5.0
        
        for keyword in urgent_keywords:
            if keyword in content:
                urgency_score = min(10.0, urgency_score + 1.0)
        
        # 判断是否时效性敏感
        time_sensitive_categories = ['politics', 'world', 'business']
        time_sensitive = news.category.value in time_sensitive_categories or urgency_score > 7.0
        
        return {
            'urgency_score': urgency_score,
            'freshness_score': freshness_score,
            'time_sensitivity': time_sensitive
        }
    
    async def _generate_recommendations(self, news: NewsModel, summary_data: Dict) -> Dict[str, Any]:
        """生成推荐信息"""
        # 估算阅读时长（基于内容长度）
        content_length = len(news.content or news.summary or news.title)
        reading_time = max(1, int(content_length / 200))  # 假设每分钟200字
        
        # 判断难度级别
        difficulty_level = "medium"
        if content_length < 500:
            difficulty_level = "easy"
        elif content_length > 2000:
            difficulty_level = "hard"
        
        # 基于分类确定目标受众
        audience_map = {
            'technology': ['技术人员', '科技爱好者', '互联网从业者'],
            'business': ['投资者', '企业家', '商业分析师'],
            'science': ['研究人员', '学生', '科学爱好者'],
            'health': ['医疗工作者', '患者', '健康关注者'],
            'sports': ['体育爱好者', '运动员', '体育媒体'],
            'politics': ['政策制定者', '政治观察者', '公民'],
            'entertainment': ['娱乐爱好者', '粉丝群体', '媒体工作者']
        }
        
        target_audience = audience_map.get(news.category.value, ['一般读者'])
        
        return {
            'reading_time': reading_time,
            'difficulty_level': difficulty_level,
            'target_audience': target_audience
        }
    
    async def _find_related_news(self, news: NewsModel) -> Dict[str, Any]:
        """查找相关新闻"""
        try:
            # 使用向量搜索查找相关新闻
            query_text = f"{news.title} {news.summary or ''}"
            results = await self.vector_service.search_similar(query_text, top_k=5)
            
            related_news_ids = []
            similarity_scores = {}
            
            for result in results:
                if result.get('news_id') != news.id:  # 排除自己
                    related_news_ids.append(result['news_id'])
                    similarity_scores[result['news_id']] = result.get('score', 0.0)
            
            return {
                'news_ids': related_news_ids,
                'similarity_scores': similarity_scores
            }
        except Exception as e:
            logger.warning(f"查找相关新闻失败: {e}")
            return {'news_ids': [], 'similarity_scores': {}}
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # 如果都失败了，返回空字典
            logger.warning(f"无法解析JSON响应: {response}")
            return {}
    
    async def _default_sentiment(self) -> Dict[str, Any]:
        """默认情感分析结果"""
        return {
            'label': SentimentLabel.NEUTRAL,
            'score': 0.0,
            'confidence': SentimentConfidence.LOW,
            'keywords': [],
            'reasons': ['未能分析']
        }
    
    async def _default_entities(self) -> Dict[str, Any]:
        """默认实体识别结果"""
        return {
            'entities': [],
            'people': [],
            'organizations': [],
            'locations': []
        }


# 服务实例
_news_card_service = None

async def get_news_card_service() -> NewsCardService:
    """获取新闻卡片服务实例"""
    global _news_card_service
    if _news_card_service is None:
        _news_card_service = NewsCardService()
    return _news_card_service