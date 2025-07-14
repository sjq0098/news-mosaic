# News Mosaic 项目设置指南

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 16.0+
- **Redis**: 6.x+
- **MongoDB**: 4.4+ 或 MySQL 8.0+
- **conda**: 推荐使用 Miniconda

### 1. 克隆项目

```bash
git clone https://github.com/your-org/news-mosaic.git
cd news-mosaic
```

### 2. 后端环境配置

#### 创建 Conda 环境
```bash
conda create -n news-mosaic python=3.10 -y
conda activate news-mosaic
```

#### 安装 Python 依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入相应的 API 密钥和数据库配置
```

### 3. 前端环境配置

```bash
cd frontend
npm install
cp .env.example .env.local
# 配置前端环境变量
```

### 4. 数据库设置

#### MongoDB (推荐)
```bash
# 启动 MongoDB 服务
mongod --dbpath /path/to/data

# 或使用 Docker
docker run -d -p 27017:27017 --name news-mosaic-mongo mongo:latest
```

#### Redis
```bash
# 启动 Redis 服务
redis-server

# 或使用 Docker
docker run -d -p 6379:6379 --name news-mosaic-redis redis:alpine
```

### 5. API 密钥配置

#### QWEN API 密钥
1. 访问 [阿里云灵积平台](https://dashscope.aliyun.com/)
2. 注册并获取 API Key
3. 在 `.env` 文件中配置 `QWEN_API_KEY`

#### Bing News Search API
1. 访问 [Azure Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/bing-news-search-api/)
2. 创建资源并获取 API Key
3. 配置 `BING_SEARCH_API_KEY`

### 6. 启动服务

#### 启动后端服务
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动 Celery 任务队列
```bash
cd backend
celery -A services.background_tasks.celery_app worker --loglevel=info
celery -A services.background_tasks.celery_app beat --loglevel=info
```

#### 启动前端服务
```bash
cd frontend
npm run dev
```

## 🛠️ 开发环境

### 代码格式化
```bash
# Python 代码格式化
cd backend
black .
isort .
flake8 .

# 前端代码格式化
cd frontend
npm run lint
npm run type-check
```

### 运行测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📦 Docker 部署

### 使用 Docker Compose
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔧 常见问题

### 1. QWEN API 连接失败
- 检查 API Key 是否正确
- 确认网络连接正常
- 查看 API 调用限制

### 2. 数据库连接问题
- 确认数据库服务已启动
- 检查连接字符串配置
- 验证用户权限

### 3. 前端构建失败
- 清除 node_modules 并重新安装
- 检查 Node.js 版本
- 更新 npm 或 yarn

## 📝 配置说明

### 环境变量
所有环境变量都在 `.env.example` 文件中有详细说明，复制并根据实际情况修改。

### 功能开关
可以通过环境变量控制功能的开启和关闭：
- `NEXT_PUBLIC_ENABLE_CHAT`: 启用聊天功能
- `NEXT_PUBLIC_ENABLE_SENTIMENT`: 启用情感分析
- `NEXT_PUBLIC_ENABLE_USER_REGISTRATION`: 启用用户注册

## 🚀 生产部署

### 性能优化
1. 启用 Redis 缓存
2. 配置 CDN 加速
3. 启用 Gzip 压缩
4. 设置合适的并发数

### 安全配置
1. 使用 HTTPS
2. 配置防火墙
3. 定期更新依赖
4. 设置访问限制

### 监控告警
1. 配置日志收集
2. 设置性能监控
3. 配置错误告警
4. 定期备份数据 