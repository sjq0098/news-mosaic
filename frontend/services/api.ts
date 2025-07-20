import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加token等认证信息
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权错误
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 新闻搜索API
export const newsApi = {
  // 搜索新闻
  searchNews: (params: {
    query: string
    num_results?: number
    language?: string
    country?: string
    time_period?: string
    category?: string
    source?: string
  }) => api.post('/api/news/search', params),

  // 获取新闻详情
  getNewsDetail: (newsId: string) => api.get(`/api/news/${newsId}`),

  // 获取相关新闻
  getRelatedNews: (newsId: string) => api.get(`/api/news/${newsId}/related`),
}

// 聊天API
export const chatApi = {
  // 发送消息
  sendMessage: (params: {
    content: string
    session_id?: string
    include_news?: boolean
    news_limit?: number
    temperature?: number
    max_tokens?: number
  }) => api.post('/api/chat/message', params),

  // 获取对话历史
  getChatHistory: (sessionId: string) => api.get(`/api/chat/history/${sessionId}`),

  // 清空对话
  clearChat: (sessionId: string) => api.delete(`/api/chat/history/${sessionId}`),

  // 智能对话
  intelligentChat: (params: {
    message: string
    user_id: string
    enable_rag?: boolean
    context_length?: number
  }) => api.post('/api/chat/intelligent', params),
}

// 新闻卡片API
export const newsCardApi = {
  // 生成新闻卡片
  generateCard: (params: {
    query: string
    user_id: string
    max_cards?: number
    enable_analysis?: boolean
  }) => api.post('/api/cards/generate', params),

  // 获取新闻卡片
  getCards: (params: {
    category?: string
    sentiment?: string
    sort_by?: string
    limit?: number
    offset?: number
  }) => api.get('/api/cards', { params }),

  // 获取卡片详情
  getCardDetail: (cardId: string) => api.get(`/api/cards/${cardId}`),

  // 删除卡片
  deleteCard: (cardId: string) => api.delete(`/api/cards/${cardId}`),

  // 更新卡片
  updateCard: (cardId: string, data: any) => api.put(`/api/cards/${cardId}`, data),
}

// 数据分析API
export const analyticsApi = {
  // 获取情感统计
  getSentimentStats: (params: {
    start_date?: string
    end_date?: string
    category?: string
  }) => api.get('/api/analytics/sentiment', { params }),

  // 获取分类统计
  getCategoryStats: (params: {
    start_date?: string
    end_date?: string
  }) => api.get('/api/analytics/categories', { params }),

  // 获取趋势数据
  getTrendData: (params: {
    start_date?: string
    end_date?: string
    granularity?: 'day' | 'week' | 'month'
  }) => api.get('/api/analytics/trends', { params }),

  // 获取热门新闻
  getTopNews: (params: {
    period?: 'day' | 'week' | 'month'
    limit?: number
  }) => api.get('/api/analytics/top-news', { params }),

  // 获取关键词云
  getKeywordCloud: (params: {
    start_date?: string
    end_date?: string
    limit?: number
  }) => api.get('/api/analytics/keywords', { params }),
}

// 用户API
export const userApi = {
  // 用户登录
  login: (credentials: {
    username: string
    password: string
  }) => api.post('/api/user/login', credentials),

  // 用户注册
  register: (userData: {
    username: string
    password: string
    email?: string
  }) => api.post('/api/user/register', userData),

  // 获取用户信息
  getUserInfo: () => api.get('/api/user/info'),

  // 更新用户信息
  updateUserInfo: (data: any) => api.put('/api/user/info', data),

  // 获取用户偏好
  getUserPreferences: () => api.get('/api/user/preferences'),

  // 更新用户偏好
  updateUserPreferences: (preferences: any) => api.put('/api/user/preferences', preferences),
}

// 情感分析API
export const sentimentApi = {
  // 分析文本情感
  analyzeText: (params: {
    text: string
    language?: string
  }) => api.post('/api/sentiment/analyze', params),

  // 批量分析
  analyzeBatch: (params: {
    texts: string[]
    language?: string
  }) => api.post('/api/sentiment/batch', params),
}

// 嵌入向量API
export const embeddingApi = {
  // 生成文本嵌入
  generateEmbedding: (params: {
    text: string
    model?: string
  }) => api.post('/api/embedding/generate', params),

  // 相似性搜索
  similaritySearch: (params: {
    query: string
    top_k?: number
    threshold?: number
  }) => api.post('/api/embedding/search', params),
}

// 管道处理API
export const pipelineApi = {
  // 完整新闻处理管道
  processNews: (params: {
    query: string
    user_id: string
    enable_cards?: boolean
    enable_chat?: boolean
  }) => api.post('/api/pipeline/process', params),

  // RAG增强管道
  ragEnhanced: (params: {
    query: string
    user_id: string
    context_length?: number
  }) => api.post('/api/pipeline/rag-enhanced', params),
}

// 导出所有API
export default api

// 类型定义
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T = any> {
  success: boolean
  data: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 错误处理工具
export const handleApiError = (error: any) => {
  if (error.response) {
    // 服务器返回错误状态码
    const { status, data } = error.response
    switch (status) {
      case 400:
        return '请求参数错误'
      case 401:
        return '未授权访问'
      case 403:
        return '访问被禁止'
      case 404:
        return '资源不存在'
      case 500:
        return '服务器内部错误'
      default:
        return data?.message || '请求失败'
    }
  } else if (error.request) {
    // 网络错误
    return '网络连接失败，请检查网络设置'
  } else {
    // 其他错误
    return error.message || '未知错误'
  }
}

// API状态检查
export const checkApiHealth = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    throw new Error('API服务不可用')
  }
}