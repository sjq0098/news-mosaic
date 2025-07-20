import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Tag, 
  Space, 
  Modal, 
  Spin, 
  Empty, 
  message,
  Input,
  Select,
  Progress,
  Tooltip
} from 'antd'
import { 
  EyeOutlined, 
  DownloadOutlined, 
  ShareAltOutlined,
  ReloadOutlined,
  PlusOutlined,
  HeartOutlined,
  CommentOutlined,
  TrophyOutlined,
  FireOutlined,
  FileTextOutlined,
  StarOutlined,
  BulbOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { newsCardApi } from '../services/api'

const { Search } = Input
const { Option } = Select

interface NewsCard {
  id: string
  title: string
  summary: string
  key_points: string[]
  sentiment_analysis: {
    label: string
    score: number
    confidence: number
  }
  topic_analysis: {
    main_topics: string[]
    keywords: string[]
  }
  source_info: {
    name: string
    credibility_score: number
    url: string
  }
  generated_at: string
  views: number
  likes: number
  category: string
  importance_score: number
}

export default function NewsCardsSection() {
  const [cards, setCards] = useState<NewsCard[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCard, setSelectedCard] = useState<NewsCard | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [filters, setFilters] = useState({
    category: 'all',
    sentiment: 'all',
    sortBy: 'generated_at'
  })

  // 获取新闻卡片
  const fetchNewsCards = async () => {
    setLoading(true)
    try {
      const response = await newsCardApi.getCards({
        category: filters.category === 'all' ? undefined : filters.category,
        sentiment: filters.sentiment === 'all' ? undefined : filters.sentiment,
        sort_by: filters.sortBy,
        limit: 20
      })

      if (response.data.success) {
        setCards(response.data.data || [])
      } else {
        message.error('获取新闻卡片失败')
      }
    } catch (error) {
      console.error('Fetch cards error:', error)
      // 使用模拟数据
      setCards(generateMockCards())
    } finally {
      setLoading(false)
    }
  }

  // 生成模拟数据
  const generateMockCards = (): NewsCard[] => {
    return Array.from({ length: 12 }, (_, index) => ({
      id: `card-${index + 1}`,
      title: `科技新闻标题 ${index + 1}：人工智能在新闻分析中的应用`,
      summary: `这是一条关于人工智能技术在新闻分析领域应用的重要新闻。该技术能够自动分析新闻内容，提取关键信息，并生成结构化的新闻卡片...`,
      key_points: [
        '人工智能技术在新闻分析中的突破',
        '自动化内容提取和分析能力提升',
        '新闻行业数字化转型加速',
        '用户体验和信息获取效率大幅改善'
      ],
      sentiment_analysis: {
        label: ['positive', 'negative', 'neutral'][index % 3],
        score: Math.random() * 2 - 1,
        confidence: 0.8 + Math.random() * 0.2
      },
      topic_analysis: {
        main_topics: ['人工智能', '新闻技术', '数字化转型'],
        keywords: ['AI', '机器学习', '自然语言处理', '新闻分析']
      },
      source_info: {
        name: ['科技日报', '人民网', '新华网', '36氪'][index % 4],
        credibility_score: 0.8 + Math.random() * 0.2,
        url: 'https://example.com'
      },
      generated_at: dayjs().subtract(index, 'hour').toISOString(),
      views: Math.floor(Math.random() * 1000) + 100,
      likes: Math.floor(Math.random() * 100) + 10,
      category: ['technology', 'business', 'politics', 'sports'][index % 4],
      importance_score: Math.random() * 100
    }))
  }

  useEffect(() => {
    fetchNewsCards()
  }, [filters])

  // 生成新闻卡片
  const handleGenerateCard = async () => {
    try {
      setLoading(true)
      const response = await newsCardApi.generateCard({
        query: '最新科技新闻',
        user_id: 'default_user',
        max_cards: 1
      })

      if (response.data.success) {
        message.success('新闻卡片生成成功')
        fetchNewsCards()
      }
    } catch (error) {
      message.error('生成新闻卡片失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取情感颜色
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'green'
      case 'negative': return 'red'
      case 'neutral': return 'blue'
      default: return 'default'
    }
  }

  // 获取情感文本
  const getSentimentText = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '正面'
      case 'negative': return '负面'
      case 'neutral': return '中性'
      default: return '未知'
    }
  }

  // 获取分类文本
  const getCategoryText = (category: string) => {
    const categoryMap: Record<string, string> = {
      technology: '科技',
      business: '商业',
      politics: '政治',
      sports: '体育',
      entertainment: '娱乐'
    }
    return categoryMap[category] || category
  }

  // 查看卡片详情
  const handleViewCard = (card: NewsCard) => {
    setSelectedCard(card)
    setModalVisible(true)
  }

  // 点赞卡片
  const handleLikeCard = (cardId: string) => {
    setCards(prev => prev.map(card => 
      card.id === cardId 
        ? { ...card, likes: card.likes + 1 }
        : card
    ))
    message.success('点赞成功')
  }

  return (
    <div className="space-y-8">
      {/* 欢迎横幅 */}
      <div className="glass-card p-8 text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center mr-4">
            <FileTextOutlined className="text-white text-2xl" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            智能新闻卡片
          </h2>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          AI生成的结构化新闻分析卡片，精准提取关键信息
        </p>
      </div>

      {/* 头部操作栏 */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-800 dark:to-pink-800 rounded-full flex items-center justify-center">
              <BulbOutlined className="text-purple-600 dark:text-purple-400 text-lg" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white m-0">
                新闻卡片集合
              </h3>
              <p className="text-gray-500 mt-1 m-0">
                共 {cards.length} 张智能生成的新闻卡片
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <Select
              value={filters.category}
              onChange={(value) => setFilters({ ...filters, category: value })}
              className="w-32"
              placeholder="选择分类"
            >
              <Option value="all">🌟 全部分类</Option>
              <Option value="technology">🔬 科技</Option>
              <Option value="business">💼 商业</Option>
              <Option value="politics">🏛️ 政治</Option>
              <Option value="sports">⚽ 体育</Option>
            </Select>
            
            <Select
              value={filters.sentiment}
              onChange={(value) => setFilters({ ...filters, sentiment: value })}
              className="w-32"
              placeholder="情感倾向"
            >
              <Option value="all">💭 全部情感</Option>
              <Option value="positive">😊 正面</Option>
              <Option value="negative">😔 负面</Option>
              <Option value="neutral">😐 中性</Option>
            </Select>
            
            <Select
              value={filters.sortBy}
              onChange={(value) => setFilters({ ...filters, sortBy: value })}
              className="w-32"
              placeholder="排序方式"
            >
              <Option value="generated_at">⏰ 最新</Option>
              <Option value="importance_score">⭐ 重要性</Option>
              <Option value="views">👁️ 热度</Option>
              <Option value="likes">❤️ 点赞数</Option>
            </Select>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchNewsCards}
              loading={loading}
              className="glass-card border-0 hover:scale-105 transition-all duration-300"
            >
              刷新
            </Button>
            
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleGenerateCard}
              loading={loading}
              className="modern-button hover:scale-105 transition-all duration-300"
            >
              生成卡片
            </Button>
          </div>
        </div>
      </div>

      {/* 卡片网格 */}
      {loading ? (
        <div className="glass-card p-16 text-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="loading-pulse">
              <FileTextOutlined className="text-6xl text-purple-500" />
            </div>
            <Spin size="large" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">正在加载新闻卡片...</p>
          </div>
        </div>
      ) : cards.length > 0 ? (
        <Row gutter={[24, 24]}>
          {cards.map((card, index) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={card.id}>
              <div className="fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                <div className="glass-card h-full overflow-hidden hover:scale-105 transition-all duration-500 group">
                  {/* 卡片头部 */}
                  <div className="p-6 pb-4">
                    <div className="flex items-center justify-between mb-3">
                      <Tag 
                        className="px-3 py-1 rounded-full border-0 bg-gradient-to-r from-blue-100 to-blue-200 dark:from-blue-800 dark:to-blue-900 text-blue-700 dark:text-blue-300 font-medium"
                      >
                        {getCategoryText(card.category)}
                      </Tag>
                      <div className="flex items-center space-x-2">
                        {card.importance_score > 70 && (
                          <Tooltip title="重要新闻">
                            <div className="w-6 h-6 bg-gradient-to-r from-orange-400 to-red-500 rounded-full flex items-center justify-center">
                              <FireOutlined className="text-white text-xs" />
                            </div>
                          </Tooltip>
                        )}
                        {card.views > 500 && (
                          <Tooltip title="热门新闻">
                            <div className="w-6 h-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                              <TrophyOutlined className="text-white text-xs" />
                            </div>
                          </Tooltip>
                        )}
                      </div>
                    </div>
                    
                    <h4 className="text-lg font-bold text-gray-900 dark:text-white line-clamp-2 mb-3 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors duration-300">
                      {card.title}
                    </h4>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">
                      {card.summary}
                    </p>
                  </div>

                  {/* 关键要点 */}
                  <div className="px-6 pb-4">
                    <div className="text-xs font-bold text-gray-500 mb-3 flex items-center">
                      <StarOutlined className="mr-2 text-yellow-500" />
                      关键要点
                    </div>
                    <div className="space-y-2">
                      {card.key_points.slice(0, 2).map((point, index) => (
                        <div key={index} className="flex items-start space-x-3">
                          <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1 leading-relaxed">
                            {point}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 情感分析 */}
                  <div className="px-6 pb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-gray-500">情感倾向</span>
                      <Tag 
                        color={getSentimentColor(card.sentiment_analysis.label)}
                        className="px-2 py-1 rounded-full border-0 font-medium text-xs"
                      >
                        {getSentimentText(card.sentiment_analysis.label)}
                      </Tag>
                    </div>
                    <Progress
                      percent={Math.abs(card.sentiment_analysis.score) * 50}
                      size="small"
                      strokeColor={{
                        '0%': '#6366f1',
                        '100%': '#8b5cf6',
                      }}
                      className="mt-1"
                      showInfo={false}
                    />
                  </div>

                  {/* 来源和统计 */}
                  <div className="px-6 py-4 border-t border-white/10 bg-white/5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2 text-gray-500">
                        <span className="font-medium">{card.source_info.name}</span>
                        <span>•</span>
                        <span>{dayjs(card.generated_at).format('MM-DD HH:mm')}</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="flex items-center text-gray-500 hover:text-blue-500 transition-colors">
                          <EyeOutlined className="mr-1" />
                          {card.views}
                        </span>
                        <span className="flex items-center text-gray-500 hover:text-red-500 transition-colors">
                          <HeartOutlined className="mr-1" />
                          {card.likes}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="px-6 py-4 border-t border-white/10">
                    <div className="flex items-center justify-between">
                      <Button
                        type="text"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewCard(card)}
                        className="text-blue-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-full px-3 transition-all duration-300"
                      >
                        查看详情
                      </Button>
                      
                      <div className="flex items-center space-x-2">
                        <Tooltip title="点赞">
                          <Button
                            type="text"
                            size="small"
                            icon={<HeartOutlined />}
                            onClick={() => handleLikeCard(card.id)}
                            className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                        </Tooltip>
                        <Tooltip title="分享">
                          <Button
                            type="text"
                            size="small"
                            icon={<ShareAltOutlined />}
                            className="text-green-500 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                        </Tooltip>
                        <Tooltip title="下载">
                          <Button
                            type="text"
                            size="small"
                            icon={<DownloadOutlined />}
                            className="text-purple-500 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-300"
                          />
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      ) : (
        <div className="glass-card p-16 text-center">
          <div className="flex flex-col items-center space-y-6">
            <div className="w-24 h-24 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 rounded-full flex items-center justify-center">
              <FileTextOutlined className="text-4xl text-gray-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">暂无新闻卡片</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">点击生成按钮创建您的第一张新闻卡片</p>
              <Button 
                type="primary" 
                size="large"
                className="modern-button"
                icon={<PlusOutlined />}
                onClick={handleGenerateCard}
              >
                生成新闻卡片
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 卡片详情模态框 */}
      <Modal
        title={
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
              <FileTextOutlined className="text-white text-sm" />
            </div>
            <span className="text-lg font-bold">新闻卡片详情</span>
          </div>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)} className="glass-card border-0">
            关闭
          </Button>,
          <Button key="download" type="primary" icon={<DownloadOutlined />} className="modern-button">
            下载卡片
          </Button>
        ]}
        width={900}
        className="modern-modal"
      >
        {selectedCard && (
          <div className="space-y-6 p-2">
            {/* 标题和分类 */}
            <div className="glass-card p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Tag className="px-3 py-1 rounded-full border-0 bg-gradient-to-r from-blue-100 to-blue-200 dark:from-blue-800 dark:to-blue-900 text-blue-700 dark:text-blue-300 font-medium">
                  {getCategoryText(selectedCard.category)}
                </Tag>
                <Tag 
                  color={getSentimentColor(selectedCard.sentiment_analysis.label)}
                  className="px-3 py-1 rounded-full border-0 font-medium"
                >
                  {getSentimentText(selectedCard.sentiment_analysis.label)}
                </Tag>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white leading-relaxed">
                {selectedCard.title}
              </h3>
            </div>

            {/* 摘要 */}
            <div className="glass-card p-6">
              <h4 className="font-bold text-gray-700 dark:text-gray-300 mb-3 flex items-center">
                <BulbOutlined className="mr-2 text-yellow-500" />
                新闻摘要
              </h4>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed text-base">
                {selectedCard.summary}
              </p>
            </div>

            {/* 关键要点 */}
            <div className="glass-card p-6">
              <h4 className="font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
                <StarOutlined className="mr-2 text-yellow-500" />
                关键要点
              </h4>
              <div className="space-y-3">
                {selectedCard.key_points.map((point, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-white/50 dark:bg-black/20 rounded-lg">
                    <div className="w-6 h-6 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs font-bold">{index + 1}</span>
                    </div>
                    <span className="text-gray-700 dark:text-gray-300 leading-relaxed">{point}</span>
                  </div>
                ))}
              </div>
            </div>

            <Row gutter={16}>
              {/* 主题分析 */}
              <Col span={12}>
                <div className="glass-card p-6 h-full">
                  <h4 className="font-bold text-gray-700 dark:text-gray-300 mb-4">主题分析</h4>
                  <div className="space-y-4">
                    <div>
                      <span className="text-sm font-medium text-gray-500 mb-2 block">主要话题：</span>
                      <div className="flex flex-wrap gap-2">
                        {selectedCard.topic_analysis.main_topics.map((topic, index) => (
                          <Tag key={index} className="px-3 py-1 rounded-full border-0 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-800 dark:to-pink-800 text-purple-700 dark:text-purple-300 font-medium">
                            {topic}
                          </Tag>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-500 mb-2 block">关键词：</span>
                      <div className="flex flex-wrap gap-2">
                        {selectedCard.topic_analysis.keywords.map((keyword, index) => (
                          <Tag key={index} className="px-2 py-1 rounded-full border-0 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs">
                            {keyword}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </Col>

              {/* 来源信息 */}
              <Col span={12}>
                <div className="glass-card p-6 h-full">
                  <h4 className="font-bold text-gray-700 dark:text-gray-300 mb-4">来源信息</h4>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-white/50 dark:bg-black/20 rounded-lg">
                      <div>
                        <div className="font-semibold text-gray-800 dark:text-gray-200">{selectedCard.source_info.name}</div>
                        <div className="text-sm text-gray-500 mt-1">
                          {dayjs(selectedCard.generated_at).format('YYYY年MM月DD日 HH:mm')}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-500">可信度评分</span>
                        <span className="text-sm font-bold text-green-600">
                          {(selectedCard.source_info.credibility_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <Progress
                        percent={selectedCard.source_info.credibility_score * 100}
                        strokeColor={{
                          '0%': '#10b981',
                          '100%': '#34d399',
                        }}
                        showInfo={false}
                      />
                    </div>
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  )
}