import React, { useState, useEffect } from 'react'
import { 
  Input, 
  Button, 
  Card, 
  Row, 
  Col, 
  Tag, 
  Space, 
  Spin, 
  Empty, 
  message,
  Select,
  DatePicker,
  Slider
} from 'antd'
import { 
  SearchOutlined, 
  ReloadOutlined, 
  FilterOutlined,
  HeartOutlined,
  ShareAltOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  FireOutlined,
  UserOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { newsApi } from '../services/api'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker

interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  url: string
  image_url?: string
  source: string
  author?: string
  published_at: string
  category: string
  keywords: string[]
  sentiment_score?: number
  sentiment_label?: string
}

interface SearchFilters {
  category?: string
  source?: string
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs] | null
  sentimentRange?: [number, number]
}

export default function NewsSearchSection() {
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [newsData, setNewsData] = useState<NewsItem[]>([])
  const [filters, setFilters] = useState<SearchFilters>({})
  const [showFilters, setShowFilters] = useState(false)
  const [total, setTotal] = useState(0)

  // 搜索新闻
  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    try {
      const response = await newsApi.searchNews({
        query,
        num_results: 20,
        language: 'zh-cn',
        country: 'cn',
        time_period: '1w',
        ...filters
      })

      if (response.data.success) {
        setNewsData(response.data.data.articles || [])
        setTotal(response.data.data.total_results || 0)
        message.success(`找到 ${response.data.data.total_results} 条相关新闻`)
      } else {
        message.error('搜索失败，请稍后重试')
      }
    } catch (error) {
      console.error('Search error:', error)
      message.error('搜索服务暂时不可用')
    } finally {
      setLoading(false)
    }
  }

  // 获取情感标签颜色
  const getSentimentColor = (sentiment?: string, score?: number) => {
    if (!sentiment) return 'default'
    switch (sentiment) {
      case 'positive': return 'green'
      case 'negative': return 'red'
      case 'neutral': return 'blue'
      default: return 'default'
    }
  }

  // 获取情感标签文本
  const getSentimentText = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return '正面'
      case 'negative': return '负面'
      case 'neutral': return '中性'
      default: return '未知'
    }
  }

  // 格式化时间
  const formatTime = (timeStr: string) => {
    return dayjs(timeStr).format('MM-DD HH:mm')
  }

  // 截取文本
  const truncateText = (text: string | undefined | null, length: number = 150) => {
    if (!text) return '暂无内容'
    return text.length > length ? text.substring(0, length) + '...' : text
  }

  return (
    <div className="space-y-8">
      {/* 欢迎横幅 */}
      <div className="glass-card p-8 text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mr-4">
            <SearchOutlined className="text-white text-2xl" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            智能新闻搜索
          </h2>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          使用AI技术快速搜索和分析新闻，获取最有价值的信息
        </p>
      </div>

      {/* 搜索栏 */}
      <div className="glass-card p-6">
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search
                placeholder="输入关键词搜索新闻..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={handleSearch}
                size="large"
                className="modern-input-search"
                enterButton={
                  <Button type="primary" className="modern-button h-12 px-8">
                    <SearchOutlined className="mr-2" />
                    搜索
                  </Button>
                }
              />
            </div>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(!showFilters)}
                className={`h-12 px-6 ${showFilters ? 'modern-button' : 'glass-card border-0'}`}
                type={showFilters ? 'primary' : 'default'}
              >
                筛选
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => handleSearch(searchQuery)}
                loading={loading}
                className="h-12 px-6 glass-card border-0"
              >
                刷新
              </Button>
            </Space>
          </div>

          {/* 筛选器 */}
          {showFilters && (
            <div className="glass-card p-6 space-y-4 border border-white/20">
              <div className="flex items-center mb-4">
                <FilterOutlined className="text-blue-500 mr-2" />
                <span className="font-semibold text-gray-700 dark:text-gray-300">高级筛选</span>
              </div>
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-600 dark:text-gray-400">新闻分类</label>
                    <Select
                      placeholder="选择分类"
                      style={{ width: '100%' }}
                      value={filters.category}
                      onChange={(value) => setFilters({ ...filters, category: value })}
                      allowClear
                      className="modern-select"
                    >
                      <Option value="technology">🔬 科技</Option>
                      <Option value="business">💼 商业</Option>
                      <Option value="politics">🏛️ 政治</Option>
                      <Option value="sports">⚽ 体育</Option>
                      <Option value="entertainment">🎭 娱乐</Option>
                    </Select>
                  </div>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-600 dark:text-gray-400">新闻来源</label>
                    <Select
                      placeholder="选择来源"
                      style={{ width: '100%' }}
                      value={filters.source}
                      onChange={(value) => setFilters({ ...filters, source: value })}
                      allowClear
                      className="modern-select"
                    >
                      <Option value="xinhua">新华网</Option>
                      <Option value="people">人民网</Option>
                      <Option value="cctv">央视网</Option>
                      <Option value="36kr">36氪</Option>
                    </Select>
                  </div>
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-600 dark:text-gray-400">时间范围</label>
                    <RangePicker
                      style={{ width: '100%' }}
                      value={filters.dateRange}
                      onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
                      className="modern-input"
                    />
                  </div>
                </Col>
                <Col xs={24} sm={12} md={4}>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-600 dark:text-gray-400">情感倾向</label>
                    <Slider
                      range
                      min={-1}
                      max={1}
                      step={0.1}
                      value={filters.sentimentRange || [-1, 1]}
                      onChange={(value) => setFilters({ ...filters, sentimentRange: value })}
                      tooltip={{ formatter: (value) => value?.toFixed(1) }}
                    />
                  </div>
                </Col>
              </Row>
            </div>
          )}
        </div>
      </div>

      {/* 搜索结果统计 */}
      {total > 0 && (
        <div className="glass-card p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <TrophyOutlined className="text-yellow-500" />
              <span className="text-gray-600 dark:text-gray-400">
                共找到 <span className="font-bold text-2xl bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">{total}</span> 条新闻
              </span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <FireOutlined className="text-red-500" />
              <span>实时更新</span>
            </div>
          </div>
        </div>
      )}

      {/* 新闻列表 */}
      <div className="space-y-6">
        {loading ? (
          <div className="glass-card p-16 text-center">
            <div className="flex flex-col items-center space-y-4">
              <div className="loading-pulse">
                <SearchOutlined className="text-6xl text-blue-500" />
              </div>
              <Spin size="large" />
              <p className="text-lg font-medium text-gray-600 dark:text-gray-400">正在搜索新闻...</p>
            </div>
          </div>
        ) : newsData.length > 0 ? (
          newsData.map((news, index) => (
            <div key={news.id} className="fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              <div className="glass-card p-6 hover:scale-[1.02] transition-all duration-500">
                <Row gutter={16}>
                  {/* 新闻图片 */}
                  {news.image_url && (
                    <Col xs={24} sm={8} md={6}>
                      <div className="w-full h-48 rounded-2xl overflow-hidden relative group">
                        <img
                          src={news.image_url}
                          alt={news.title}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      </div>
                    </Col>
                  )}
                  
                  {/* 新闻内容 */}
                  <Col xs={24} sm={news.image_url ? 16 : 24} md={news.image_url ? 18 : 24}>
                    <div className="space-y-4 h-full flex flex-col">
                      {/* 标题和来源 */}
                      <div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 line-clamp-2 hover:text-blue-600 transition-colors duration-300">
                          <a 
                            href={news.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            {news.title}
                          </a>
                        </h3>
                        <div className="flex items-center space-x-3 text-sm text-gray-500">
                          <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full font-medium">
                            {news.source}
                          </span>
                          {news.author && (
                            <span className="flex items-center">
                              <UserOutlined className="mr-1" />
                              {news.author}
                            </span>
                          )}
                          <span className="flex items-center">
                            <ClockCircleOutlined className="mr-1" />
                            {formatTime(news.published_at)}
                          </span>
                        </div>
                      </div>

                      {/* 摘要 */}
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed flex-1">
                        {truncateText(news.summary || news.content)}
                      </p>

                      {/* 标签和操作 */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 flex-wrap gap-2">
                          {/* 分类标签 */}
                          <Tag 
                            color="blue" 
                            className="px-3 py-1 rounded-full font-medium border-0 bg-gradient-to-r from-blue-100 to-blue-200 dark:from-blue-800 dark:to-blue-900"
                          >
                            {news.category}
                          </Tag>
                          
                          {/* 情感标签 */}
                          {news.sentiment_label && (
                            <Tag 
                              color={getSentimentColor(news.sentiment_label, news.sentiment_score)}
                              className="px-3 py-1 rounded-full font-medium border-0"
                            >
                              {getSentimentText(news.sentiment_label)}
                              {news.sentiment_score && (
                                <span className="ml-1 opacity-75">
                                  ({news.sentiment_score.toFixed(2)})
                                </span>
                              )}
                            </Tag>
                          )}

                          {/* 关键词标签 */}
                          {news.keywords?.slice(0, 3).map((keyword, index) => (
                            <Tag 
                              key={index} 
                              className="text-xs px-2 py-1 rounded-full border-0 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
                            >
                              {keyword}
                            </Tag>
                          ))}
                        </div>

                        {/* 操作按钮 */}
                        <Space>
                          <Button 
                            type="text" 
                            icon={<EyeOutlined />} 
                            size="small"
                            className="text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                          <Button 
                            type="text" 
                            icon={<HeartOutlined />} 
                            size="small"
                            className="text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                          <Button 
                            type="text" 
                            icon={<ShareAltOutlined />} 
                            size="small"
                            className="text-gray-500 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                        </Space>
                      </div>
                    </div>
                  </Col>
                </Row>
              </div>
            </div>
          ))
        ) : (
          <div className="glass-card p-16 text-center">
            <div className="flex flex-col items-center space-y-6">
              <div className="w-24 h-24 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 rounded-full flex items-center justify-center">
                <SearchOutlined className="text-4xl text-gray-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">暂无搜索结果</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">尝试使用不同的关键词或调整筛选条件</p>
                <Button 
                  type="primary" 
                  size="large"
                  className="modern-button"
                  onClick={() => handleSearch('最新新闻')}
                >
                  浏览最新新闻
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}