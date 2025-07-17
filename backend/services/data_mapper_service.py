"""
数据映射服务 - 将QWEN返回的中文数据转换为Pydantic模型格式
"""

import re
from typing import Dict, Any, List, Optional
from loguru import logger

from models.news_card import ImportanceLevel, CredibilityLevel
from models.sentiment import SentimentLabel, SentimentConfidence


class DataMapperService:
    """数据映射服务 - 处理QWEN返回数据的格式转换"""
    
    def __init__(self):
        # 重要性级别映射
        self.importance_mapping = {
            "极高": ImportanceLevel.CRITICAL,
            "非常高": ImportanceLevel.CRITICAL,
            "重大": ImportanceLevel.CRITICAL,
            "高": ImportanceLevel.HIGH,
            "重要": ImportanceLevel.HIGH,
            "中等": ImportanceLevel.MEDIUM,
            "一般": ImportanceLevel.MEDIUM,
            "普通": ImportanceLevel.MEDIUM,
            "低": ImportanceLevel.LOW,
            "较低": ImportanceLevel.LOW,
            "最低": ImportanceLevel.MINIMAL,
            "微小": ImportanceLevel.MINIMAL,
            # 英文值直接映射
            "critical": ImportanceLevel.CRITICAL,
            "high": ImportanceLevel.HIGH,
            "medium": ImportanceLevel.MEDIUM,
            "low": ImportanceLevel.LOW,
            "minimal": ImportanceLevel.MINIMAL
        }
        
        # 可信度级别映射
        self.credibility_mapping = {
            "已验证": CredibilityLevel.VERIFIED,
            "官方": CredibilityLevel.VERIFIED,
            "权威": CredibilityLevel.VERIFIED,
            "可靠": CredibilityLevel.RELIABLE,
            "可信": CredibilityLevel.RELIABLE,
            "中等": CredibilityLevel.MODERATE,
            "一般": CredibilityLevel.MODERATE,
            "中等可信": CredibilityLevel.MODERATE,
            "中等偏低": CredibilityLevel.MODERATE,
            "中等偏低可信度": CredibilityLevel.MODERATE,
            "低": CredibilityLevel.QUESTIONABLE,
            "较低": CredibilityLevel.QUESTIONABLE,
            "不可信": CredibilityLevel.UNVERIFIED,
            "未验证": CredibilityLevel.UNVERIFIED,
            # 英文值直接映射
            "verified": CredibilityLevel.VERIFIED,
            "reliable": CredibilityLevel.RELIABLE,
            "moderate": CredibilityLevel.MODERATE,
            "questionable": CredibilityLevel.QUESTIONABLE,
            "unverified": CredibilityLevel.UNVERIFIED
        }
        
        # 情感标签映射
        self.sentiment_mapping = {
            "正面": SentimentLabel.POSITIVE,
            "积极": SentimentLabel.POSITIVE,
            "乐观": SentimentLabel.POSITIVE,
            "负面": SentimentLabel.NEGATIVE,
            "消极": SentimentLabel.NEGATIVE,
            "悲观": SentimentLabel.NEGATIVE,
            "中性": SentimentLabel.NEUTRAL,
            "客观": SentimentLabel.NEUTRAL,
            "平和": SentimentLabel.NEUTRAL,
            # 英文值直接映射
            "positive": SentimentLabel.POSITIVE,
            "negative": SentimentLabel.NEGATIVE,
            "neutral": SentimentLabel.NEUTRAL
        }
        
        # 情感置信度映射
        self.confidence_mapping = {
            "高": SentimentConfidence.HIGH,
            "很高": SentimentConfidence.HIGH,
            "非常高": SentimentConfidence.HIGH,
            "中等": SentimentConfidence.MEDIUM,
            "一般": SentimentConfidence.MEDIUM,
            "普通": SentimentConfidence.MEDIUM,
            "低": SentimentConfidence.LOW,
            "较低": SentimentConfidence.LOW,
            "很低": SentimentConfidence.LOW,
            # 英文值直接映射
            "high": SentimentConfidence.HIGH,
            "medium": SentimentConfidence.MEDIUM,
            "low": SentimentConfidence.LOW
        }
        
        # 难度级别映射
        self.difficulty_mapping = {
            "简单": "easy",
            "容易": "easy",
            "基础": "easy",
            "中等": "medium",
            "一般": "medium",
            "普通": "medium",
            "困难": "hard",
            "复杂": "hard",
            "高级": "hard",
            # 英文值直接映射
            "easy": "easy",
            "medium": "medium",
            "hard": "hard"
        }
    
    def map_importance_level(self, value: Any) -> ImportanceLevel:
        """映射重要性级别"""
        if isinstance(value, ImportanceLevel):
            return value
        
        if isinstance(value, str):
            # 直接匹配
            if value in self.importance_mapping:
                return self.importance_mapping[value]
            
            # 模糊匹配
            value_lower = value.lower()
            for key, mapped_value in self.importance_mapping.items():
                if key.lower() in value_lower:
                    return mapped_value
        
        # 默认返回中等重要性
        logger.warning(f"无法映射重要性级别: {value}，使用默认值 medium")
        return ImportanceLevel.MEDIUM
    
    def map_credibility_level(self, value: Any) -> CredibilityLevel:
        """映射可信度级别"""
        if isinstance(value, CredibilityLevel):
            return value
        
        if isinstance(value, str):
            # 直接匹配
            if value in self.credibility_mapping:
                return self.credibility_mapping[value]
            
            # 模糊匹配
            value_lower = value.lower()
            for key, mapped_value in self.credibility_mapping.items():
                if key.lower() in value_lower:
                    return mapped_value
        
        # 默认返回中等可信度
        logger.warning(f"无法映射可信度级别: {value}，使用默认值 moderate")
        return CredibilityLevel.MODERATE
    
    def map_sentiment_label(self, value: Any) -> SentimentLabel:
        """映射情感标签"""
        if isinstance(value, SentimentLabel):
            return value
        
        if isinstance(value, str):
            # 直接匹配
            if value in self.sentiment_mapping:
                return self.sentiment_mapping[value]
            
            # 模糊匹配
            value_lower = value.lower()
            for key, mapped_value in self.sentiment_mapping.items():
                if key.lower() in value_lower:
                    return mapped_value
        
        # 默认返回中性
        logger.warning(f"无法映射情感标签: {value}，使用默认值 neutral")
        return SentimentLabel.NEUTRAL
    
    def map_sentiment_confidence(self, value: Any) -> SentimentConfidence:
        """映射情感置信度"""
        if isinstance(value, SentimentConfidence):
            return value
        
        if isinstance(value, str):
            # 直接匹配
            if value in self.confidence_mapping:
                return self.confidence_mapping[value]
            
            # 模糊匹配
            value_lower = value.lower()
            for key, mapped_value in self.confidence_mapping.items():
                if key.lower() in value_lower:
                    return mapped_value
        
        # 默认返回中等置信度
        logger.warning(f"无法映射情感置信度: {value}，使用默认值 medium")
        return SentimentConfidence.MEDIUM
    
    def map_difficulty_level(self, value: Any) -> str:
        """映射难度级别"""
        if isinstance(value, str):
            # 直接匹配
            if value in self.difficulty_mapping:
                return self.difficulty_mapping[value]
            
            # 模糊匹配
            value_lower = value.lower()
            for key, mapped_value in self.difficulty_mapping.items():
                if key.lower() in value_lower:
                    return mapped_value
        
        # 默认返回中等难度
        logger.warning(f"无法映射难度级别: {value}，使用默认值 medium")
        return "medium"
    
    def extract_reading_time(self, value: Any) -> int:
        """提取阅读时间（分钟）"""
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            # 提取数字
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[0])
        
        # 默认返回1分钟
        logger.warning(f"无法提取阅读时间: {value}，使用默认值 1")
        return 1
    
    def convert_dict_to_list(self, value: Any) -> List[str]:
        """将字典格式的数据转换为列表格式 - 修复版本，保留完整内容"""
        if isinstance(value, list):
            return value
        
        if isinstance(value, dict):
            result = []
            for key, item_data in value.items():
                if isinstance(item_data, dict):
                    # 处理嵌套字典：组合有用信息
                    if 'type' in item_data:
                        result.append(f"{key}: {item_data['type']}")
                    elif 'description' in item_data:
                        result.append(f"{key}: {item_data['description']}")
                    else:
                        # 组合字典中的所有信息
                        sub_info = []
                        for k, v in item_data.items():
                            if isinstance(v, (str, int, float)) and str(v).strip():
                                sub_info.append(f"{k}={v}")
                        if sub_info:
                            result.append(f"{key}: {', '.join(sub_info)}")
                        else:
                            result.append(key)
                elif isinstance(item_data, str) and item_data.strip():
                    # 对于字符串值，完整保留键值对信息
                    # 这对于重要性原因和可信度因素很关键
                    result.append(f"{key}: {item_data}")
                elif item_data is not None:
                    # 其他非空值
                    result.append(f"{key}: {str(item_data)}")
                else:
                    # 只有键没有值的情况
                    result.append(key)
            return result
        
        if isinstance(value, str) and value.strip():
            # 处理字符串格式的数据
            value = value.strip()
            if '、' in value:
                return [item.strip() for item in value.split('、') if item.strip()]
            elif ',' in value:
                return [item.strip() for item in value.split(',') if item.strip()]
            elif ';' in value:
                return [item.strip() for item in value.split(';') if item.strip()]
            elif '|' in value:
                return [item.strip() for item in value.split('|') if item.strip()]
            else:
                return [value]
        
        # 对于其他类型或空值，返回空列表
        return []
    
    def convert_entities_format(self, entities_data: Any) -> List[Dict[str, Any]]:
        """转换实体数据格式"""
        if isinstance(entities_data, list):
            return entities_data
        
        if isinstance(entities_data, dict):
            result = []
            for entity_name, entity_info in entities_data.items():
                if isinstance(entity_info, dict):
                    entity_item = {
                        "entity": entity_name,
                        "entity_type": entity_info.get("type", "unknown"),
                        "mention_count": entity_info.get("count", 1),
                        "confidence": entity_info.get("confidence", 0.8)
                    }
                    result.append(entity_item)
                else:
                    result.append({
                        "entity": entity_name,
                        "entity_type": "unknown",
                        "mention_count": 1,
                        "confidence": 0.8
                    })
            return result
        
        return []
    
    def normalize_qwen_response(self, qwen_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化QWEN响应数据"""
        try:
            normalized = {}
            
            # 复制简单字段
            simple_fields = [
                "news_id", "card_id", "summary", "enhanced_summary", 
                "importance_score", "credibility_score", "sentiment_score",
                "urgency_score", "freshness_score", "time_sensitivity",
                "generation_model", "generation_time"
            ]
            
            for field in simple_fields:
                if field in qwen_data:
                    normalized[field] = qwen_data[field]
            
            # 映射枚举字段
            if "importance_level" in qwen_data:
                normalized["importance_level"] = self.map_importance_level(qwen_data["importance_level"])
            
            if "credibility_level" in qwen_data:
                normalized["credibility_level"] = self.map_credibility_level(qwen_data["credibility_level"])
            
            if "sentiment_label" in qwen_data:
                normalized["sentiment_label"] = self.map_sentiment_label(qwen_data["sentiment_label"])
            
            if "sentiment_confidence" in qwen_data:
                normalized["sentiment_confidence"] = self.map_sentiment_confidence(qwen_data["sentiment_confidence"])
            
            if "difficulty_level" in qwen_data:
                normalized["difficulty_level"] = self.map_difficulty_level(qwen_data["difficulty_level"])
            
            if "reading_time_minutes" in qwen_data:
                normalized["reading_time_minutes"] = self.extract_reading_time(qwen_data["reading_time_minutes"])
            
            # 转换列表字段 - 使用改进的转换方法
            list_fields = [
                "key_points", "keywords", "hashtags", "emotional_keywords",
                "importance_reasons", "credibility_factors", "people", 
                "organizations", "locations", "target_audience", "related_news_ids"
            ]
            
            for field in list_fields:
                if field in qwen_data:
                    converted_list = self.convert_dict_to_list(qwen_data[field])
                    normalized[field] = converted_list
                    logger.debug(f"转换字段 {field}: {type(qwen_data[field])} -> {type(converted_list)} ({len(converted_list)} 项)")
            
            # 转换实体数据
            if "entities" in qwen_data:
                normalized["entities"] = self.convert_entities_format(qwen_data["entities"])
            
            # 处理主题数据
            if "themes" in qwen_data:
                themes_data = qwen_data["themes"]
                if isinstance(themes_data, dict):
                    normalized["themes"] = {
                        "primary_theme": themes_data.get("primary_theme", ""),
                        "secondary_themes": themes_data.get("secondary_themes", []),
                        "theme_confidence": themes_data.get("theme_confidence", 0.8)
                    }
            
            # 处理其他字典字段
            if "similarity_scores" in qwen_data:
                normalized["similarity_scores"] = qwen_data["similarity_scores"] if isinstance(qwen_data["similarity_scores"], dict) else {}
            
            if "metadata" in qwen_data:
                normalized["metadata"] = qwen_data["metadata"] if isinstance(qwen_data["metadata"], dict) else {}
            
            logger.info("QWEN响应数据标准化完成")
            return normalized
            
        except Exception as e:
            logger.error(f"标准化QWEN响应数据失败: {e}")
            raise


# 创建全局实例
data_mapper = DataMapperService() 