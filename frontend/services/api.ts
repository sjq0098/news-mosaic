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

// 注意：已删除独立的新闻搜索、聊天、新闻卡片、数据分析API
// 这些功能现在都整合在统一的新闻处理流水线中

// 用户API
export const userApi = {
  // 用户登录
  login: (credentials: {
    username: string
    password: string
  }) => api.post('/api/user/auth/login', credentials),

  // 用户注册
  register: (userData: {
    username: string
    password: string
    email: string
    nickname?: string
  }) => api.post('/api/user/auth/register', userData),

  // 刷新令牌
  refreshToken: (refreshToken: string) => api.post('/api/user/auth/refresh', { refresh_token: refreshToken }),

  // 获取用户档案
  getUserProfile: () => api.get('/api/user/profile'),

  // 更新用户档案
  updateUserProfile: (data: {
    nickname?: string
    avatar_url?: string
    bio?: string
    preferences?: any
  }) => api.put('/api/user/profile', data),

  // 获取用户偏好
  getUserPreferences: () => api.get('/api/user/preferences'),

  // 更新用户偏好
  updateUserPreferences: (preferences: any) => api.put('/api/user/preferences', preferences),

  // 修改密码
  changePassword: (data: {
    old_password: string
    new_password: string
  }) => api.post('/api/user/change-password', data),

  // 获取用户活动摘要
  getUserActivity: () => api.get('/api/user/activity'),

  // 增加用户统计
  incrementUserStat: (statType: string) => api.post(`/api/user/stats/increment/${statType}`),

  // 健康检查
  healthCheck: () => api.get('/api/user/health'),

  // 个性化功能
  getUserPersonalizationQuery: () => api.get('/api/user/personalization/news-query'),
  recordUserInteraction: (data: {
    type: string
    content_id: string
    metadata?: any
  }) => api.post('/api/user/personalization/interaction', data),
  getUserReadingHistory: (limit?: number) => api.get('/api/user/personalization/history', { params: { limit } }),
  getTrendingTopics: () => api.get('/api/user/personalization/trending'),
  getRecommendedKeywords: () => api.get('/api/user/personalization/recommended-keywords'),
}

// 注意：已删除情感分析、嵌入向量、管道处理、统一新闻处理API
// 这些功能现在都整合在新闻处理流水线中

// 新闻处理流水线API
export const newsPipelineApi = {
  // 完整流水线处理
  processNews: (params: {
    query: string
    user_id?: string
    num_results?: number
    language?: string
    country?: string
    time_period?: string
    enable_storage?: boolean
    enable_vectorization?: boolean
    enable_ai_analysis?: boolean
    enable_card_generation?: boolean
    enable_sentiment_analysis?: boolean
    enable_user_memory?: boolean
    max_cards?: number
    include_related_news?: boolean
    personalization_level?: number
  }) => api.post('/api/news-pipeline/process', params, { timeout: 120000 }), // 2分钟超时

  // 快速处理
  quickProcess: (query: string, num_results?: number) =>
    api.post('/api/news-pipeline/quick-process', null, {
      params: { query, num_results }
    }),

  // 搜索并分析
  searchAndAnalyze: (params: {
    query: string
    enable_cards?: boolean
    enable_sentiment?: boolean
    max_results?: number
  }) => api.post('/api/news-pipeline/search-and-analyze', params),

  // 批量处理
  batchProcess: (queries: string[]) =>
    api.post('/api/news-pipeline/batch-process', { queries }),

  // 获取处理状态
  getStatus: (pipelineId: string) =>
    api.get(`/api/news-pipeline/status/${pipelineId}`),

  // 健康检查
  healthCheck: () => api.get('/api/news-pipeline/health'),
}

// 增强RAG对话API
export const enhancedChatApi = {
  // RAG对话
  chatWithRAG: (params: {
    user_id?: string
    message: string
    session_id?: string
    max_context_news?: number
    similarity_threshold?: number
    temperature?: number
    max_tokens?: number
    use_user_memory?: boolean
    include_related_news?: boolean
    enable_personalization?: boolean
  }) => api.post('/api/enhanced-chat/chat', params),

  // 快速对话
  quickChat: (message: string, session_id?: string) =>
    api.post('/api/enhanced-chat/quick-chat', null, {
      params: { message, session_id }
    }),

  // 新闻问答
  newsQA: (params: {
    question: string
    news_topic?: string
    max_sources?: number
  }) => api.post('/api/enhanced-chat/news-qa', params),

  // 获取对话历史
  getConversationHistory: (sessionId: string, limit?: number) =>
    api.get(`/api/enhanced-chat/conversation/${sessionId}`, {
      params: { limit }
    }),

  // 删除对话
  deleteConversation: (sessionId: string) =>
    api.delete(`/api/enhanced-chat/conversation/${sessionId}`),

  // 获取用户对话列表
  getUserConversations: (limit?: number) =>
    api.get('/api/enhanced-chat/user/conversations', {
      params: { limit }
    }),

  // 健康检查
  healthCheck: () => api.get('/api/enhanced-chat/health'),
}

// 用户记忆管理API
export const userMemoryApi = {
  // 记录用户行为
  recordBehavior: (params: {
    user_id?: string
    action: string
    content: string
    metadata?: any
  }) => api.post('/api/user-memory/record-behavior', params),

  // 快速记录行为
  quickRecord: (action: string, content: string, target_id?: string) =>
    api.post('/api/user-memory/quick-record', null, {
      params: { action, content, target_id }
    }),

  // 获取个性化内容
  getPersonalization: (params: {
    user_id?: string
    query?: string
    content_type?: string
    max_recommendations?: number
  }) => api.post('/api/user-memory/personalization', params),

  // 获取用户兴趣档案
  getInterestProfile: () => api.get('/api/user-memory/interest-profile'),

  // 获取推荐内容
  getRecommendations: (content_type?: string, max_count?: number) =>
    api.get('/api/user-memory/recommendations', {
      params: { content_type, max_count }
    }),

  // 获取个性化查询
  getPersonalizedQueries: (base_query?: string) =>
    api.get('/api/user-memory/personalized-queries', {
      params: { base_query }
    }),

  // 清除用户记忆
  clearMemory: () => api.delete('/api/user-memory/clear-memory'),

  // 获取记忆分析
  getAnalytics: () => api.get('/api/user-memory/analytics'),

  // 健康检查
  healthCheck: () => api.get('/api/user-memory/health'),
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