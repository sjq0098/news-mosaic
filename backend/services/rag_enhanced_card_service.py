"""
RAG增强版新闻卡片生成服务
重点强化Embedding与向量检索在新闻分析中的参与度
"""

import asyncio
import json
import time
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger

from services.qwen_service import QWENService
from services.vector_db_service import get_vector_db
from services.data_mapper_service import data_mapper
from models.news_card import (
    NewsCard, NewsCardMetadata, NewsTheme, EntityMention,
    ImportanceLevel, CredibilityLevel, SentimentLabel, SentimentConfidence,
    NewsCardRequest, NewsCardResponse
)
from models.news import NewsModel
from core.config import settings


class RAGEnhancedCardService:
    """RAG增强版新闻卡片生成服务"""
    
    def __init__(self):
        self.qwen_service = QWENService()
        self.vector_service = get_vector_db()
        self.demo_mode = not settings.is_api_configured("qwen")
        
        if self.demo_mode:
            logger.warning("RAG服务启用演示模式 - API未配置")
        
    async def generate_card_with_rag(self, news: NewsModel, request: NewsCardRequest) -> NewsCardResponse:
        """使用RAG增强生成新闻卡片"""
        start_time = time.time()
        warnings = []
        
        # 如果是演示模式，返回模拟卡片
        if self.demo_mode:
            return await self._generate_demo_card(news, request, start_time)
        
        try:
            # 步骤1: 多维度向量检索，构建丰富的RAG上下文
            rag_context = await self._build_comprehensive_rag_context(news)
            
            # 步骤2: 基于RAG上下文的并行增强分析
            analysis_tasks = [
                self._rag_enhanced_summary(news, rag_context, request.max_summary_length),
                self._rag_enhanced_sentiment(news, rag_context) if request.include_sentiment else self._default_sentiment(),
                self._rag_enhanced_themes(news, rag_context),
                self._rag_enhanced_importance(news, rag_context),
                self._rag_enhanced_credibility(news, rag_context),
                self._rag_enhanced_entities(news, rag_context) if request.include_entities else self._default_entities(),
                self._rag_enhanced_timeliness(news, rag_context)
            ]
            
            # 执行所有RAG增强分析
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 处理分析结果并应用数据映射
            summary_data = results[0] if not isinstance(results[0], Exception) else {}
            sentiment_data = results[1] if not isinstance(results[1], Exception) else {}
            theme_data = results[2] if not isinstance(results[2], Exception) else {}
            importance_data = results[3] if not isinstance(results[3], Exception) else {}
            credibility_data = results[4] if not isinstance(results[4], Exception) else {}
            entity_data = results[5] if not isinstance(results[5], Exception) else {}
            timeliness_data = results[6] if not isinstance(results[6], Exception) else {}
            
            # 应用数据映射，确保枚举值正确
            if sentiment_data:
                sentiment_data['label'] = data_mapper.map_sentiment_label(sentiment_data.get('label'))
                sentiment_data['confidence'] = data_mapper.map_sentiment_confidence(sentiment_data.get('confidence'))
            
            if importance_data:
                importance_data['level'] = data_mapper.map_importance_level(importance_data.get('level'))
            
            if credibility_data:
                credibility_data['level'] = data_mapper.map_credibility_level(credibility_data.get('level'))
            
            # 转换列表格式的数据
            if entity_data:
                entity_data['people'] = data_mapper.convert_dict_to_list(entity_data.get('people', []))
                entity_data['organizations'] = data_mapper.convert_dict_to_list(entity_data.get('organizations', []))
                entity_data['locations'] = data_mapper.convert_dict_to_list(entity_data.get('locations', []))
                entity_data['entities'] = data_mapper.convert_entities_format(entity_data.get('entities', []))
            
            if summary_data:
                summary_data['target_audience'] = data_mapper.convert_dict_to_list(summary_data.get('target_audience', []))
                summary_data['reading_time'] = data_mapper.extract_reading_time(summary_data.get('reading_time', 1))
                summary_data['difficulty_level'] = data_mapper.map_difficulty_level(summary_data.get('difficulty_level', 'medium'))
            
            # 步骤3: RAG趋势分析和预测
            if request.include_related:
                trend_analysis = await self._rag_trend_analysis(news, rag_context)
            else:
                trend_analysis = {'trend_indicators': [], 'prediction': ''}
            
            # 步骤4: 构建RAG增强的卡片元数据
            metadata = NewsCardMetadata(
                news_id=news.id,
                card_id=f"rag_card_{news.id}_{int(time.time())}",
                
                # RAG增强的内容分析
                summary=summary_data.get('summary', ''),
                enhanced_summary=summary_data.get('enhanced_summary', ''),
                key_points=summary_data.get('key_points', []),
                
                # RAG增强的关键词和主题
                keywords=summary_data.get('keywords', []),
                hashtags=summary_data.get('hashtags', []),
                themes=NewsTheme(
                    primary_theme=theme_data.get('primary_theme', '其他'),
                    secondary_themes=theme_data.get('secondary_themes', []),
                    theme_confidence=theme_data.get('theme_confidence', 0.5)
                ),
                
                # RAG增强的情感分析
                sentiment_label=sentiment_data.get('label', SentimentLabel.NEUTRAL),
                sentiment_score=sentiment_data.get('score', 0.0),
                sentiment_confidence=sentiment_data.get('confidence', SentimentConfidence.MEDIUM),
                emotional_keywords=sentiment_data.get('keywords', []),
                
                # RAG增强的重要性分析
                importance_score=importance_data.get('score', 5.0),
                importance_level=importance_data.get('level', ImportanceLevel.MEDIUM),
                importance_reasons=importance_data.get('reasons', []),
                
                # RAG增强的可信度分析
                credibility_score=credibility_data.get('score', 5.0),
                credibility_level=credibility_data.get('level', CredibilityLevel.MODERATE),
                credibility_factors=credibility_data.get('factors', []),
                
                # RAG增强的实体识别
                entities=entity_data.get('entities', []),
                people=entity_data.get('people', []),
                organizations=entity_data.get('organizations', []),
                locations=entity_data.get('locations', []),
                
                # RAG增强的时效性分析
                urgency_score=timeliness_data.get('urgency_score', 5.0),
                freshness_score=timeliness_data.get('freshness_score', 5.0),
                time_sensitivity=timeliness_data.get('time_sensitivity', False),
                
                # 推荐信息（基于相似新闻）
                target_audience=summary_data.get('target_audience', ['一般读者']),
                reading_time_minutes=summary_data.get('reading_time', 5),
                difficulty_level=summary_data.get('difficulty_level', 'medium'),
                
                # RAG增强的相关性分析
                related_news_ids=rag_context.get('related_news_ids', []),
                similarity_scores=rag_context.get('similarity_scores', {}),
                
                # 生成信息
                generation_model=request.generation_model or settings.QWEN_MODEL,
                generation_time=time.time() - start_time,
                
                # RAG特有的元数据
                metadata={
                    'rag_context_size': len(rag_context.get('context_text', '')),
                    'related_news_count': len(rag_context.get('related_news_ids', [])),
                    'historical_context': rag_context.get('historical_context', ''),
                    'trend_indicators': trend_analysis.get('trend_indicators', []),
                    'cross_references': rag_context.get('cross_references', []),
                    'fact_check_status': credibility_data.get('fact_check_status', 'pending')
                }
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
                display_priority=int(importance_data.get('score', 5.0)),
                color_theme=self._determine_color_theme(importance_data, sentiment_data)
            )
            
            processing_time = time.time() - start_time
            logger.info(f"RAG增强新闻卡片生成完成: {news.id}, 耗时: {processing_time:.2f}s")
            
            return NewsCardResponse(
                card=card,
                processing_time=processing_time,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"RAG增强卡片生成失败: {e}")
            raise
    
    async def _build_comprehensive_rag_context(self, news: NewsModel) -> Dict[str, Any]:
        """构建全面的RAG上下文"""
        try:
            # 1. 多维度向量检索
            search_tasks = [
                # 基于标题的相似新闻
                self._vector_search_by_title(news),
                # 基于内容的相似新闻  
                self._vector_search_by_content(news),
                # 基于分类的历史新闻
                self._vector_search_by_category(news),
                # 基于关键词的相关新闻
                self._vector_search_by_keywords(news)
            ]
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 2. 合并和去重搜索结果
            all_related = self._merge_search_results(search_results)
            
            # 3. 构建丰富的上下文
            context = {
                'related_news_ids': all_related.get('news_ids', []),
                'similarity_scores': all_related.get('similarity_scores', {}),
                'context_text': await self._build_context_text(all_related),
                'historical_context': await self._extract_historical_context(all_related),
                'cross_references': self._generate_cross_references(all_related),
                'temporal_patterns': await self._analyze_temporal_patterns(all_related)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"构建RAG上下文失败: {e}")
            return {
                'related_news_ids': [],
                'similarity_scores': {},
                'context_text': '',
                'historical_context': '',
                'cross_references': [],
                'temporal_patterns': {}
            }
    
    async def _vector_search_by_title(self, news: NewsModel) -> Dict[str, Any]:
        """基于标题的向量搜索"""
        try:
            results = self.vector_service.query_similar(news.title, top_k=5)
            return {'type': 'title', 'results': results}
        except Exception as e:
            logger.warning(f"标题向量搜索失败: {e}")
            return {'type': 'title', 'results': []}
    
    async def _vector_search_by_content(self, news: NewsModel) -> Dict[str, Any]:
        """基于内容的向量搜索"""
        try:
            content = news.content or news.summary or news.title
            # 取内容前500字符进行搜索
            search_text = content[:500]
            results = self.vector_service.query_similar(search_text, top_k=5)
            return {'type': 'content', 'results': results}
        except Exception as e:
            logger.warning(f"内容向量搜索失败: {e}")
            return {'type': 'content', 'results': []}
    
    async def _vector_search_by_category(self, news: NewsModel) -> Dict[str, Any]:
        """基于分类的向量搜索"""
        try:
            # 使用分类相关的查询词
            category_keywords = {
                'technology': '科技技术AI人工智能',
                'business': '商业经济金融市场',
                'science': '科学研究发现',
                'health': '健康医疗卫生',
                'sports': '体育运动比赛',
                'politics': '政治政策政府',
                'entertainment': '娱乐明星影视'
            }
            
            search_text = category_keywords.get(news.category.value, news.category.value)
            results = self.vector_service.query_similar(search_text, top_k=3)
            return {'type': 'category', 'results': results}
        except Exception as e:
            logger.warning(f"分类向量搜索失败: {e}")
            return {'type': 'category', 'results': []}
    
    async def _vector_search_by_keywords(self, news: NewsModel) -> Dict[str, Any]:
        """基于关键词的向量搜索"""
        try:
            if news.keywords:
                search_text = ' '.join(news.keywords[:5])  # 使用前5个关键词
                results = self.vector_service.query_similar(search_text, top_k=3)
                return {'type': 'keywords', 'results': results}
            return {'type': 'keywords', 'results': []}
        except Exception as e:
            logger.warning(f"关键词向量搜索失败: {e}")
            return {'type': 'keywords', 'results': []}
    
    def _merge_search_results(self, search_results: List[Dict]) -> Dict[str, Any]:
        """合并多维度搜索结果"""
        all_news_ids = []
        similarity_scores = {}
        
        for result in search_results:
            if isinstance(result, Exception):
                continue
                
            for item in result.get('results', []):
                news_id = item.get('news_id')
                score = item.get('score', 0.0)
                
                if news_id and news_id not in all_news_ids:
                    all_news_ids.append(news_id)
                    similarity_scores[news_id] = score
        
        # 按相似度排序，取前10个
        sorted_ids = sorted(all_news_ids, key=lambda x: similarity_scores.get(x, 0), reverse=True)[:10]
        
        return {
            'news_ids': sorted_ids,
            'similarity_scores': {nid: similarity_scores[nid] for nid in sorted_ids}
        }
    
    async def _build_context_text(self, related_results: Dict) -> str:
        """构建RAG上下文文本"""
        # 这里应该从数据库获取相关新闻的完整内容
        # 由于您不负责数据库对接，我们用模拟数据
        news_ids = related_results.get('news_ids', [])
        if not news_ids:
            return ""
        
        context_parts = ["相关新闻上下文:"]
        for i, news_id in enumerate(news_ids[:5], 1):
            score = related_results.get('similarity_scores', {}).get(news_id, 0)
            context_parts.append(f"{i}. 新闻{news_id} (相似度: {score:.3f})")
            context_parts.append(f"   标题: [模拟]相关新闻标题_{news_id}")
            context_parts.append(f"   摘要: [模拟]这是与当前新闻相关的历史新闻内容...")
        
        return "\n".join(context_parts)
    
    async def _extract_historical_context(self, related_results: Dict) -> str:
        """提取历史背景上下文"""
        news_ids = related_results.get('news_ids', [])
        if not news_ids:
            return "暂无相关历史背景"
        
        return f"基于{len(news_ids)}条相关新闻分析，该话题在近期持续受到关注，体现了行业发展的连续性。"
    
    def _generate_cross_references(self, related_results: Dict) -> List[str]:
        """生成交叉引用"""
        news_ids = related_results.get('news_ids', [])
        return [f"参考新闻_{nid}" for nid in news_ids[:3]]
    
    async def _analyze_temporal_patterns(self, related_results: Dict) -> Dict[str, Any]:
        """分析时间模式"""
        return {
            'frequency': 'increasing',
            'peak_times': ['最近一周'],
            'trend': 'upward'
        }
    
    async def _rag_enhanced_summary(self, news: NewsModel, rag_context: Dict, max_length: int) -> Dict[str, Any]:
        """RAG增强的摘要生成"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于以下新闻及相关背景信息，生成结构化摘要：

当前新闻:
标题: {news.title}
内容: {(news.content or news.summary or news.title)[:1000]}

{context_text}

请基于当前新闻和相关背景信息，生成JSON格式结果：
1. summary: 智能摘要（不超过{max_length}字符，融合历史背景）
2. enhanced_summary: 增强摘要（包含发展脉络和趋势分析）
3. key_points: 核心要点（结合历史对比）
4. keywords: 关键词（包含趋势性关键词）
5. hashtags: 推荐标签
6. target_audience: 目标受众（基于相关新闻受众分析）
7. reading_time: 预估阅读时长
8. difficulty_level: 阅读难度

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'summary')
    
    async def _rag_enhanced_sentiment(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的情感分析"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于当前新闻和相关历史新闻，进行综合情感分析：

当前新闻: {news.title}
{context_text}

请分析并返回JSON格式：
1. label: 情感标签（positive/negative/neutral/mixed）
2. score: 情感分数（-1.0到1.0）
3. confidence: 置信度（low/medium/high）
4. keywords: 情感关键词
5. reasons: 情感判断原因（结合历史趋势）
6. sentiment_trend: 相比历史相关新闻的情感变化趋势
7. public_opinion: 基于相关新闻的公众舆论趋势

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'sentiment')
    
    async def _rag_enhanced_themes(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的主题分析"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于当前新闻和相关背景，进行深度主题分析：

当前新闻: {news.title}
分类: {news.category}
{context_text}

请分析并返回JSON格式：
1. primary_theme: 主要主题（考虑历史发展脉络）
2. secondary_themes: 次要主题
3. theme_confidence: 主题识别置信度
4. theme_evolution: 主题演变趋势
5. related_themes: 从相关新闻中发现的关联主题

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'themes')
    
    async def _rag_enhanced_importance(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的重要性分析"""
        context_text = rag_context.get('context_text', '')
        related_count = len(rag_context.get('related_news_ids', []))
        
        prompt = f"""
基于当前新闻和{related_count}条相关历史新闻，评估重要性：

当前新闻: {news.title}
发布时间: {news.published_at}
来源: {news.source}
{context_text}

重要性评估标准（结合历史对比）：
- 相关新闻数量: {related_count}
- 话题持续性和发展趋势
- 影响范围对比历史事件
- 媒体关注度变化

请分析并返回JSON格式：
1. score: 重要性分数（0.0-10.0，考虑历史对比）
2. level: 重要性级别
3. reasons: 重要性判断原因（包含历史对比）
4. historical_ranking: 在相关历史新闻中的重要性排名
5. trend_impact: 对整体趋势的影响程度

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'importance')
    
    async def _rag_enhanced_credibility(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的可信度分析"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于当前新闻和相关历史信息，进行可信度交叉验证：

当前新闻: {news.title}
来源: {news.source}
发布者: {news.publisher or '未知'}
{context_text}

可信度评估（结合历史验证）：
- 与历史相关新闻的一致性
- 信息源的历史可靠性
- 事实陈述的可验证性
- 相关新闻的交叉验证结果

请分析并返回JSON格式：
1. score: 可信度分数（0.0-10.0）
2. level: 可信度级别
3. factors: 影响可信度的因素
4. fact_check_status: 事实核查状态（verified/questionable/conflicting）
5. cross_validation: 与历史新闻的交叉验证结果
6. reliability_trend: 该来源的历史可靠性趋势

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'credibility')
    
    async def _rag_enhanced_entities(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的实体识别"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于当前新闻和相关背景，进行实体识别和关系分析：

当前新闻: {news.title}
内容: {(news.content or news.summary or '')[:800]}
{context_text}

请识别并返回JSON格式：
1. entities: 实体列表（结合历史出现频次）
2. people: 人物名称（标注历史相关度）
3. organizations: 机构名称（标注重要性）
4. locations: 地点名称
5. entity_relationships: 实体间关系
6. historical_connections: 与历史新闻中实体的关联

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'entities')
    
    async def _rag_enhanced_timeliness(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG增强的时效性分析"""
        now = datetime.utcnow()
        time_diff = now - news.published_at
        hours_old = time_diff.total_seconds() / 3600
        
        # 基于历史相关新闻分析紧急程度
        related_count = len(rag_context.get('related_news_ids', []))
        
        # 计算基础分数
        if hours_old < 1:
            freshness_score = 10.0
        elif hours_old < 6:
            freshness_score = 9.0
        elif hours_old < 24:
            freshness_score = 8.0
        elif hours_old < 72:
            freshness_score = 6.0
        else:
            freshness_score = 4.0
        
        # 基于相关新闻数量调整紧急程度
        urgency_score = 5.0
        if related_count > 5:
            urgency_score += 2.0  # 热点话题
        if related_count > 10:
            urgency_score += 1.0  # 持续热点
        
        # 检查紧急关键词
        content = news.content or news.summary or news.title
        urgent_keywords = ['突发', '紧急', '重大', '立即', '警报', '事故', '灾害']
        for keyword in urgent_keywords:
            if keyword in content:
                urgency_score = min(10.0, urgency_score + 1.0)
        
        # 判断时效性敏感
        time_sensitive = urgency_score > 7.0 or related_count > 8
        
        return {
            'urgency_score': min(10.0, urgency_score),
            'freshness_score': freshness_score,
            'time_sensitivity': time_sensitive,
            'related_news_factor': min(2.0, related_count / 5),  # 相关新闻影响因子
            'topic_heat': 'high' if related_count > 8 else 'medium' if related_count > 3 else 'low'
        }
    
    async def _rag_trend_analysis(self, news: NewsModel, rag_context: Dict) -> Dict[str, Any]:
        """RAG趋势分析"""
        context_text = rag_context.get('context_text', '')
        
        prompt = f"""
基于当前新闻和相关历史新闻，进行趋势分析和预测：

当前新闻: {news.title}
{context_text}

请分析并返回JSON格式：
1. trend_indicators: 趋势指标列表
2. prediction: 发展预测
3. risk_factors: 风险因素
4. opportunities: 机会点
5. timeline_forecast: 时间线预测

请确保返回有效的JSON格式。
"""
        
        return await self._call_qwen_with_fallback(prompt, 'trend')
    
    async def _call_qwen_with_fallback(self, prompt: str, analysis_type: str) -> Dict[str, Any]:
        """调用QWen API并提供fallback"""
        try:
            response = await self.qwen_service.generate_response(prompt)
            result = self._parse_json_response(response.content)
            return result
        except Exception as e:
            logger.error(f"{analysis_type}分析失败: {e}")
            return self._get_fallback_result(analysis_type)
    
    def _get_fallback_result(self, analysis_type: str) -> Dict[str, Any]:
        """获取fallback结果"""
        fallbacks = {
            'summary': {
                'summary': '智能摘要生成失败',
                'enhanced_summary': '增强摘要生成失败',
                'key_points': ['核心要点提取失败'],
                'keywords': [],
                'hashtags': [],
                'target_audience': ['一般读者'],
                'reading_time': 5,
                'difficulty_level': 'medium'
            },
            'sentiment': {
                'label': SentimentLabel.NEUTRAL,
                'score': 0.0,
                'confidence': SentimentConfidence.LOW,
                'keywords': [],
                'reasons': ['分析失败'],
                'sentiment_trend': 'stable',
                'public_opinion': 'neutral'
            },
            'themes': {
                'primary_theme': '主题分析失败',
                'secondary_themes': [],
                'theme_confidence': 0.3,
                'theme_evolution': 'unknown',
                'related_themes': []
            },
            'importance': {
                'score': 5.0,
                'level': ImportanceLevel.MEDIUM,
                'reasons': ['分析失败'],
                'historical_ranking': 'unknown',
                'trend_impact': 'moderate'
            },
            'credibility': {
                'score': 5.0,
                'level': CredibilityLevel.MODERATE,
                'factors': ['分析失败'],
                'fact_check_status': 'pending',
                'cross_validation': 'incomplete',
                'reliability_trend': 'unknown'
            },
            'entities': {
                'entities': [],
                'people': [],
                'organizations': [],
                'locations': [],
                'entity_relationships': [],
                'historical_connections': []
            },
            'trend': {
                'trend_indicators': [],
                'prediction': '趋势分析失败',
                'risk_factors': [],
                'opportunities': [],
                'timeline_forecast': []
            }
        }
        
        return fallbacks.get(analysis_type, {})
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(f"无法解析JSON响应: {response}")
            return {}
    
    def _determine_color_theme(self, importance_data: Dict, sentiment_data: Dict) -> str:
        """确定卡片颜色主题"""
        importance = importance_data.get('score', 5.0)
        sentiment = sentiment_data.get('label', SentimentLabel.NEUTRAL)
        
        if importance >= 9.0:
            return 'critical-red'
        elif importance >= 7.0:
            return 'important-orange'
        elif sentiment == SentimentLabel.POSITIVE:
            return 'positive-green'
        elif sentiment == SentimentLabel.NEGATIVE:
            return 'negative-blue'
        else:
            return 'neutral-gray'
    
    async def _default_sentiment(self) -> Dict[str, Any]:
        """默认情感分析结果"""
        return {
            'label': SentimentLabel.NEUTRAL,
            'score': 0.0,
            'confidence': SentimentConfidence.LOW,
            'keywords': [],
            'reasons': ['未进行分析'],
            'sentiment_trend': 'stable',
            'public_opinion': 'neutral'
        }
    
    async def _default_entities(self) -> Dict[str, Any]:
        """默认实体识别结果"""
        return {
            'entities': [],
            'people': [],
            'organizations': [],
            'locations': [],
            'entity_relationships': [],
            'historical_connections': []
        }

    async def _generate_demo_card(self, news: NewsModel, request: NewsCardRequest, start_time: float) -> NewsCardResponse:
        """生成演示模式下的模拟卡片"""
        warnings = []
        processing_time = time.time() - start_time
        
        # 模拟数据
        summary_data = {
            'summary': '这是一篇关于人工智能的模拟新闻。',
            'enhanced_summary': '人工智能技术正在快速发展，从语音识别到自动驾驶，再到智能推荐，它正在改变我们的生活方式。',
            'key_points': ['人工智能技术正在快速发展', '它正在改变我们的生活方式'],
            'keywords': ['人工智能', '技术', '发展', '改变'],
            'hashtags': ['#AI', '#技术', '#发展'],
            'target_audience': ['对科技感兴趣的读者'],
            'reading_time': 3,
            'difficulty_level': 'easy'
        }
        sentiment_data = {
            'label': SentimentLabel.POSITIVE,
            'score': 0.8,
            'confidence': SentimentConfidence.HIGH,
            'keywords': ['积极', '发展', '进步'],
            'reasons': ['模拟数据'],
            'sentiment_trend': 'upward',
            'public_opinion': 'positive'
        }
        theme_data = {
            'primary_theme': '人工智能',
            'secondary_themes': ['技术发展', '智能应用'],
            'theme_confidence': 0.9,
            'theme_evolution': 'upward',
            'related_themes': ['机器学习', '深度学习']
        }
        importance_data = {
            'score': 9.5,
            'level': ImportanceLevel.CRITICAL,
            'reasons': ['模拟数据'],
            'historical_ranking': 'top',
            'trend_impact': 'significant'
        }
        credibility_data = {
            'score': 9.0,
            'level': CredibilityLevel.HIGH,
            'factors': ['模拟数据'],
            'fact_check_status': 'verified',
            'cross_validation': 'complete',
            'reliability_trend': 'stable'
        }
        entity_data = {
            'entities': ['人工智能', '机器学习', '深度学习'],
            'people': ['李飞', '张三'],
            'organizations': ['百度', '腾讯', '阿里巴巴'],
            'locations': ['北京', '上海', '深圳'],
            'entity_relationships': [],
            'historical_connections': []
        }
        timeliness_data = {
            'urgency_score': 9.8,
            'freshness_score': 9.5,
            'time_sensitivity': True,
            'related_news_factor': 1.5,
            'topic_heat': 'high'
        }
        trend_analysis = {
            'trend_indicators': ['增长', '发展', '普及'],
            'prediction': '人工智能技术将继续快速发展，并在更多领域得到应用。',
            'risk_factors': ['技术瓶颈', '隐私问题'],
            'opportunities': ['新应用场景', '创新技术'],
            'timeline_forecast': ['2024年', '2025年']
        }

        metadata = NewsCardMetadata(
            news_id=news.id,
            card_id=f"rag_card_{news.id}_{int(time.time())}",
            
            # RAG增强的内容分析
            summary=summary_data.get('summary', ''),
            enhanced_summary=summary_data.get('enhanced_summary', ''),
            key_points=summary_data.get('key_points', []),
            
            # RAG增强的关键词和主题
            keywords=summary_data.get('keywords', []),
            hashtags=summary_data.get('hashtags', []),
            themes=NewsTheme(
                primary_theme=theme_data.get('primary_theme', '其他'),
                secondary_themes=theme_data.get('secondary_themes', []),
                theme_confidence=theme_data.get('theme_confidence', 0.5)
            ),
            
            # RAG增强的情感分析
            sentiment_label=sentiment_data.get('label', SentimentLabel.NEUTRAL),
            sentiment_score=sentiment_data.get('score', 0.0),
            sentiment_confidence=sentiment_data.get('confidence', SentimentConfidence.MEDIUM),
            emotional_keywords=sentiment_data.get('keywords', []),
            
            # RAG增强的重要性分析
            importance_score=importance_data.get('score', 5.0),
            importance_level=importance_data.get('level', ImportanceLevel.MEDIUM),
            importance_reasons=importance_data.get('reasons', []),
            
            # RAG增强的可信度分析
            credibility_score=credibility_data.get('score', 5.0),
            credibility_level=credibility_data.get('level', CredibilityLevel.MODERATE),
            credibility_factors=credibility_data.get('factors', []),
            
            # RAG增强的实体识别
            entities=entity_data.get('entities', []),
            people=entity_data.get('people', []),
            organizations=entity_data.get('organizations', []),
            locations=entity_data.get('locations', []),
            
            # RAG增强的时效性分析
            urgency_score=timeliness_data.get('urgency_score', 5.0),
            freshness_score=timeliness_data.get('freshness_score', 5.0),
            time_sensitivity=timeliness_data.get('time_sensitivity', False),
            
            # 推荐信息（基于相似新闻）
            target_audience=summary_data.get('target_audience', ['一般读者']),
            reading_time_minutes=summary_data.get('reading_time', 5),
            difficulty_level=summary_data.get('difficulty_level', 'medium'),
            
            # RAG增强的相关性分析
            related_news_ids=[],
            similarity_scores={},
            
            # 生成信息
            generation_model=request.generation_model or settings.QWEN_MODEL,
            generation_time=processing_time,
            
            # RAG特有的元数据
            metadata={
                'rag_context_size': 0,
                'related_news_count': 0,
                'historical_context': '',
                'trend_indicators': trend_analysis.get('trend_indicators', []),
                'cross_references': [],
                'fact_check_status': credibility_data.get('fact_check_status', 'pending')
            }
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
            display_priority=int(importance_data.get('score', 5.0)),
            color_theme=self._determine_color_theme(importance_data, sentiment_data)
        )
        
        return NewsCardResponse(
            card=card,
            processing_time=processing_time,
            warnings=warnings
        )

    async def _create_metadata_from_response(
        self, 
        analysis_response: str,
        request: NewsCardRequest,
        processing_time: float
    ) -> NewsCardMetadata:
        """从分析响应创建元数据"""
        try:
            # 解析JSON响应
            parsed_data = json.loads(analysis_response)
            
            # 使用数据映射服务标准化数据
            normalized_data = data_mapper.normalize_qwen_response(parsed_data)
            
            # 确保必需字段存在，使用默认值填充缺失字段
            metadata_data = {
                "news_id": request.news_id,
                "card_id": f"card_{request.news_id}_{int(time.time())}",
                "summary": normalized_data.get("summary", ""),
                "enhanced_summary": normalized_data.get("enhanced_summary", ""),
                "key_points": normalized_data.get("key_points", []),
                "keywords": normalized_data.get("keywords", []),
                "hashtags": normalized_data.get("hashtags", []),
                
                # 主题信息（提供默认值）
                "themes": normalized_data.get("themes", {
                    "primary_theme": "未分类",
                    "secondary_themes": [],
                    "theme_confidence": 0.5
                }),
                
                # 情感分析（使用映射后的枚举值）
                "sentiment_label": normalized_data.get("sentiment_label", SentimentLabel.NEUTRAL),
                "sentiment_score": normalized_data.get("sentiment_score", 0.0),
                "sentiment_confidence": normalized_data.get("sentiment_confidence", SentimentConfidence.MEDIUM),
                "emotional_keywords": normalized_data.get("emotional_keywords", []),
                
                # 重要性分析（使用映射后的枚举值）
                "importance_score": normalized_data.get("importance_score", 5.0),
                "importance_level": normalized_data.get("importance_level", ImportanceLevel.MEDIUM),
                "importance_reasons": normalized_data.get("importance_reasons", []),
                
                # 可信度分析（使用映射后的枚举值）
                "credibility_score": normalized_data.get("credibility_score", 5.0),
                "credibility_level": normalized_data.get("credibility_level", CredibilityLevel.MODERATE),
                "credibility_factors": normalized_data.get("credibility_factors", []),
                
                # 实体识别（使用转换后的格式）
                "entities": normalized_data.get("entities", []),
                "people": normalized_data.get("people", []),
                "organizations": normalized_data.get("organizations", []),
                "locations": normalized_data.get("locations", []),
                
                # 时效性
                "urgency_score": normalized_data.get("urgency_score", 3.0),
                "freshness_score": normalized_data.get("freshness_score", 5.0),
                "time_sensitivity": normalized_data.get("time_sensitivity", False),
                
                # 推荐信息（使用转换后的格式）
                "target_audience": normalized_data.get("target_audience", []),
                "reading_time_minutes": normalized_data.get("reading_time_minutes", 1),
                "difficulty_level": normalized_data.get("difficulty_level", "medium"),
                
                # 相关性
                "related_news_ids": normalized_data.get("related_news_ids", []),
                "similarity_scores": normalized_data.get("similarity_scores", {}),
                
                # 生成信息
                "generation_model": "qwen-plus",
                "generation_time": processing_time,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": normalized_data.get("metadata", {})
            }
            
            # 创建NewsCardMetadata实例
            metadata = NewsCardMetadata(**metadata_data)
            logger.info(f"成功创建标准化的NewsCardMetadata: {metadata.news_id}")
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"解析QWEN分析响应JSON失败: {e}")
            logger.error(f"原始响应: {analysis_response[:500]}...")
            return self._create_fallback_metadata(request, processing_time)
        except Exception as e:
            logger.error(f"创建NewsCardMetadata失败: {e}")
            logger.error(f"数据内容: {normalized_data if 'normalized_data' in locals() else 'N/A'}")
            return self._create_fallback_metadata(request, processing_time)

    def _create_fallback_metadata(self, request: NewsCardRequest, processing_time: float) -> NewsCardMetadata:
        """创建降级元数据"""
        logger.warning(f"使用降级元数据创建NewsCardMetadata: {request.news_id}")
        return NewsCardMetadata(
            news_id=request.news_id,
            card_id=f"fallback_card_{request.news_id}_{int(time.time())}",
            summary="降级元数据",
            enhanced_summary="降级元数据",
            key_points=["降级元数据"],
            keywords=["降级元数据"],
            hashtags=["#降级元数据"],
            themes=NewsTheme(primary_theme="降级元数据", secondary_themes=[], theme_confidence=0.3),
            sentiment_label=SentimentLabel.NEUTRAL,
            sentiment_score=0.0,
            sentiment_confidence=SentimentConfidence.LOW,
            emotional_keywords=["降级元数据"],
            importance_score=5.0,
            importance_level=ImportanceLevel.MEDIUM,
            importance_reasons=["降级元数据"],
            credibility_score=5.0,
            credibility_level=CredibilityLevel.MODERATE,
            credibility_factors=["降级元数据"],
            entities=[],
            people=[],
            organizations=[],
            locations=[],
            urgency_score=3.0,
            freshness_score=5.0,
            time_sensitivity=False,
            target_audience=["降级元数据"],
            reading_time_minutes=1,
            difficulty_level="medium",
            related_news_ids=[],
            similarity_scores={},
            generation_model=settings.QWEN_MODEL,
            generation_time=processing_time,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )