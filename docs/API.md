# News Mosaic API 文档

## 📋 概述

News Mosaic 提供 RESTful API 服务，支持新闻搜索、聊天对话、情感分析等功能。

**Base URL**: `http://localhost:8000/api/v1`

## 🔐 认证

### JWT Token 认证
```http
Authorization: Bearer <your_jwt_token>
```

### 获取 Token
```http
POST /api/v1/user/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

## 📰 新闻 API

### 搜索新闻
```http
GET /api/v1/news/search?query=AI&limit=20&offset=0
```

**参数**:
- `query` (string): 搜索关键词
- `category` (string, optional): 新闻分类
- `source` (string, optional): 新闻来源
- `limit` (int): 返回数量限制 (1-100)
- `offset` (int): 偏移量

**响应**:
```json
{
  "items": [
    {
      "id": "news_id",
      "title": "新闻标题",
      "summary": "新闻摘要",
      "url": "https://example.com/news",
      "published_at": "2024-01-01T12:00:00Z",
      "sentiment_score": 0.7,
      "sentiment_label": "positive"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "has_next": true
}
```

### 获取最新新闻
```http
GET /api/v1/news/latest?limit=10&category=technology
```

### 获取热门新闻
```http
GET /api/v1/news/trending?limit=10&hours=24
```

### 获取新闻详情
```http
GET /api/v1/news/{news_id}
```

### 新闻统计
```http
GET /api/v1/news/stats?days=7
```

## 💬 聊天 API

### 发送消息
```http
POST /api/v1/chat/send
Content-Type: application/json
Authorization: Bearer <token>

{
  "session_id": "session_id", // 可选，新会话时为空
  "content": "请分析一下最近的AI新闻",
  "include_news": true,
  "news_limit": 5,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**响应**:
```json
{
  "session": {
    "id": "session_id",
    "title": "AI新闻分析",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "messages": [
    {
      "id": "msg_id",
      "role": "user",
      "content": "请分析一下最近的AI新闻",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "msg_id_2",
      "role": "assistant",
      "content": "根据最新的AI新闻分析...",
      "created_at": "2024-01-01T12:00:01Z",
      "news_ids": ["news_1", "news_2"]
    }
  ],
  "response_time": 2.5,
  "tokens_used": 150
}
```

### 获取会话列表
```http
GET /api/v1/chat/sessions?page=1&size=20
Authorization: Bearer <token>
```

### 获取会话消息
```http
GET /api/v1/chat/sessions/{session_id}/messages?limit=50
Authorization: Bearer <token>
```

### 重新生成回复
```http
POST /api/v1/chat/sessions/{session_id}/regenerate
Authorization: Bearer <token>

{
  "temperature": 0.8
}
```

## 😊 情感分析 API

### 分析文本情感
```http
POST /api/v1/sentiment/analyze
Content-Type: application/json

{
  "text": "这是一条非常好的消息！",
  "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
  "include_keywords": true,
  "include_reasons": true
}
```

**响应**:
```json
{
  "analysis": {
    "id": "analysis_id",
    "text": "这是一条非常好的消息！",
    "label": "positive",
    "score": 0.85,
    "confidence": 0.92,
    "confidence_level": "high",
    "positive_score": 0.85,
    "negative_score": 0.05,
    "neutral_score": 0.10,
    "keywords": ["好的", "消息"],
    "reasons": ["积极情感词汇", "感叹号表示兴奋"],
    "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest"
  },
  "processing_time": 0.5
}
```

### 批量情感分析
```http
POST /api/v1/sentiment/batch-analyze
Content-Type: application/json

{
  "texts": [
    "这是第一条文本",
    "这是第二条文本"
  ],
  "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest"
}
```

### 获取情感统计
```http
GET /api/v1/sentiment/stats?days=7&category=technology
```

### 获取情感趋势
```http
GET /api/v1/sentiment/trends?days=30
```

## 👤 用户 API

### 用户注册
```http
POST /api/v1/user/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "nickname": "测试用户"
}
```

### 用户登录
```http
POST /api/v1/user/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

### 获取用户资料
```http
GET /api/v1/user/profile
Authorization: Bearer <token>
```

### 更新用户资料
```http
PUT /api/v1/user/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "nickname": "新昵称",
  "bio": "个人简介"
}
```

### 修改密码
```http
POST /api/v1/user/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "old_password",
  "new_password": "new_password"
}
```

### 获取用户偏好
```http
GET /api/v1/user/preferences
Authorization: Bearer <token>
```

### 更新用户偏好
```http
PUT /api/v1/user/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "preferred_categories": ["technology", "science"],
  "language": "zh-CN",
  "items_per_page": 20
}
```

## 📊 系统 API

### 健康检查
```http
GET /api/v1/health
```

### QWEN 模型状态
```http
GET /api/v1/chat/models/qwen/status
```

## 🚫 错误处理

### 错误响应格式
```json
{
  "error": "错误类型",
  "message": "详细错误信息",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 常见错误码
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `429 Too Many Requests`: 请求频率限制
- `500 Internal Server Error`: 服务器内部错误

## 📝 使用示例

### Python 示例
```python
import requests

# 搜索新闻
response = requests.get(
    "http://localhost:8000/api/v1/news/search",
    params={"query": "AI", "limit": 5}
)
news = response.json()

# 情感分析
response = requests.post(
    "http://localhost:8000/api/v1/sentiment/analyze",
    json={"text": "这是一条测试消息"}
)
sentiment = response.json()
```

### JavaScript 示例
```javascript
// 搜索新闻
const newsResponse = await fetch(
  'http://localhost:8000/api/v1/news/search?query=AI&limit=5'
);
const news = await newsResponse.json();

// 发送聊天消息
const chatResponse = await fetch(
  'http://localhost:8000/api/v1/chat/send',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify({
      content: '请分析最新的AI新闻',
      include_news: true
    })
  }
);
const chat = await chatResponse.json();
```

## 🔄 API 版本

当前 API 版本: `v1`

版本更新将通过 URL 路径区分: `/api/v2/...` 