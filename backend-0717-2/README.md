# 新闻助手系统快速启动指南

## 🚀 前置准备

### 1. 环境要求
- Python 3.8+
- MongoDB 4.0+
- Internet 连接

### 2. API 密钥申请

#### SerpAPI 密钥（新闻搜索）
1. 访问 https://serpapi.com/
2. 注册账号并获取 API Key
3. 免费额度：100次/月

#### 通义千问 API 密钥（智能对话）
1. 访问 https://dashscope.console.aliyun.com/
2. 注册阿里云账号
3. 开通通义千问服务
4. 获取 API Key

## 📦 安装依赖

```bash
# 进入项目目录
cd backend-0717

# 安装Python依赖
pip install -r requirements.txt
```

## ⚙️ 配置设置

### 1. 复制配置文件
```bash
cp .env.example .env
```

### 2. 编辑配置文件
编辑 `.env` 文件，填入您的 API 密钥：

```env
# 必填项
SERPAPI_KEY=your_serpapi_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 可选项（使用默认值即可）
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=news_mosaic
```

## 🎯 启动系统

### 方式一：Web API 服务
```bash
python main.py
```
访问 http://localhost:8000/docs 查看 API 文档

### 方式二：控制台调试
```bash
# 方法1：直接运行
python console_debug.py

# 方法2：双击批处理文件
debug_console.bat
```

## 🎮 使用示例

### 控制台调试示例
```
您: 搜索今天的科技新闻
助手: ✅ 搜索完成！找到12篇新闻，新增保存8篇

您: 我对人工智能感兴趣
助手: ✅ 已将「人工智能」添加到您的兴趣中

您: 我的兴趣
助手: 📋 您当前的兴趣偏好：科技、人工智能
```

### API 调用示例
```bash
# 智能对话
curl -X POST "http://localhost:8000/api/v1/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session",
    "message": "搜索今天的体育新闻"
  }'
```

## 🔧 故障排除

### 常见问题

1. **API Key 错误**
   - 检查 `.env` 文件中的密钥是否正确
   - 确认密钥有足够的调用额度

2. **MongoDB 连接失败**
   - 确认 MongoDB 服务已启动
   - 检查连接地址是否正确

3. **依赖安装失败**
   - 升级 pip：`pip install --upgrade pip`
   - 使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log
```

## 📚 功能说明

### 核心功能
- **智能新闻搜索**：基于关键词搜索最新新闻
- **兴趣管理**：自动记录和管理用户兴趣偏好
- **智能对话**：支持自然语言交互
- **数据入库**：自动去重并保存新闻到数据库

### 支持的命令
- 新闻搜索：`搜索科技新闻`、`最近有什么新闻`
- 兴趣管理：`我对体育感兴趣`、`删除科技兴趣`、`我的兴趣`
- 系统命令：`help`、`status`、`quit`

## 🔗 相关链接
- API 文档：http://localhost:8000/docs
- 项目仓库：[您的项目地址]
- 技术支持：[您的联系方式]

---
祝您使用愉快！如有问题，请查看日志或联系技术支持。
