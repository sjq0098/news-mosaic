# news-mosaic  
多模态大模型新闻搜索分析工具

## 一、项目简介  
本项目基于大模型 API（如 QWEN、DeepSeek）与 RAG、用户记忆机制，构建一个免爬虫的新闻检索、摘要生成、情感分析和多轮问答的 Web 应用。用户可输入任意主题（如“学术领域有哪些新闻”），系统自动调用新闻搜索 API 拉取海量实时新闻，生成结构化“新闻卡片”（时间、事件、观点、链接），并提供情感倾向打分，支持用户对单条或多条新闻进行进一步追问。

## 二、核心功能  
1. **新闻搜索 & 索引**  
   - 调用第三方新闻搜索 API（Bing News Search、SerpAPI 等）  
   - 实时拉取并去重、存储新闻元数据  
2. **向量化 & RAG 检索**  
   - 利用大模型生成新闻摘要片段的 Embedding  
   - 存入向量数据库（Pinecone/Weaviate），支持快速召回  
3. **摘要卡片生成**  
   - 调用 LLM 生成结构化卡片：  
     - 时间（YYYY-MM-DD）  
     - 事件概述  
     - 观点提炼  
     - 原文链接  
4. **情感分析**  
   - 并行调用情感分类接口，为每条新闻打分（正/中/负向）  
5. **用户记忆 & 推荐**  
   - 持久化记录用户查询、收藏与追问历史  
   - 基于用户画像优化检索结果排序  
6. **多轮对话问答**  
   - 保持对话上下文与记忆，支持连续追问  
   - 动态召回相关新闻片段，生成深度回答  

## 三、技术架构

```markdown
浏览器（React/Next.js + Ant Design）
↓ REST / WebSocket
后端服务（FastAPI）
├─ 搜索模块（Bing News API）
├─ 向量索引 & RAG（Pinecone/Weaviate）
├─ LLM 调度（QWEN + LangChain）
├─ 情感分析微服务
├─ 用户记忆与画像（MongoDB/MySQL + Redis）
└─ 异步任务（Celery + Redis）
```


## 四、环境依赖  
- Node.js ≥ 16.x  
- Python ≥ 3.9  
- MongoDB ≥ 4.4  
- Redis ≥ 6.x  
- Pinecone/Weaviate 账号  
- SerpAPI Key  
- QWEN API Key  

## 五、快速启动

1. **克隆仓库**  
   ```bash
   git clone https://github.com/sjq0098/news-mosaic.git
   cd news-mosaic
  ```

2. **后端配置**

   ```bash
   cd backend
   cp .env.example .env
   # 修改 .env 中的 API_KEYS、数据库连接等配置
   pip install -r requirements.txt
   ```

3. **前端配置**

   ```bash
   cd frontend
   cp .env.example .env
   npm install
   ```

4. **启动服务**

   * 后端：

     ```bash
     cd backend
     python main:app --reload
     ```
   * 前端：

     ```bash
     cd frontend
     npm run dev
     ```

5. **访问**
   打开浏览器，访问 [http://localhost:3000](http://localhost:3000)

## 六、项目目录结构

```
├── backend/               # 后端服务
│   ├── api/               # 路由与控制器
│   ├── core/              # 配置与初始化
│   ├── services/          # 搜索、RAG、LLM、情感分析等模块
│   ├── tasks/             # 定时任务
│   ├── models/            # Pydantic 模型、DB ORM
│   └── main.py            # 入口文件
├── frontend/              # 前端项目
│   ├── pages/             # Next.js 页面
│   ├── components/        # 通用组件（搜索框、卡片、对话窗）
│   └── services/          # API 调用封装
├── docs/                  # 设计文档、ER 图、流程图
└── README.md              # 本文件
```

## 七、分工说明

* **A（后端·新闻采集 & 存储）**

  * 集成第三方新闻搜索 API（Bing News/SerpAPI）
  * 定时拉取与去重任务（Celery/cron）
  * 新闻元数据入库（MongoDB 或 MySQL）

* **B（后端·向量检索 & LLM 调度）**

  * 文本切片与 Embedding 生成（QWEN‑Embedding/DeepSeek）
  * 向量库管理与 RAG 检索接口（Pinecone/Weaviate）
  * 摘要卡片与情感分析 API（QWEN/DeepSeek + 自定义 Prompt）

* **C（前端·界面与交互）**

  * React/Next.js + Ant Design 页面搭建
  * 搜索框、卡片列表、多轮对话组件开发
  * 与后端 REST API 的联调

* **D（本地集成 & 测试）**

  * 搭建本地开发环境（数据库、Redis、向量库模拟）
  * 不同用户记忆数据管理分片
  * 编写并维护项目文档（ER 图、流程图、API 说明）
  * 核心功能联调、单元测试与接口测试
  * 提供本地启动脚本或 Docker Compose 配置

## 八、开发与提交流程

1. Fork → Feature 分支开发
2. 提交 PR → 同组互审 → 合并 `develop`
3. 定期将 `develop` 合并至 `main`
4. 编写 **单元测试** & **接口测试**

## 九、贡献者

* A（后端）：[@memberA](https://github.com/memberA)
* B（后端）：[@memberB](https://github.com/memberB)
* C（前端）：[@memberC](https://github.com/memberC)
* D（本地集成 & 测试）：[@memberD](https://github.com/memberD)

```

---


