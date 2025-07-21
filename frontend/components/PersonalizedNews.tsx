import React, { useState, useEffect } from 'react'
import { 
  Card, 
  List, 
  Tag, 
  Button, 
  Space, 
  message, 
  Skeleton,
  Empty,
  Tooltip,
  Badge
} from 'antd'
import { 
  HeartOutlined, 
  ShareAltOutlined, 
  EyeOutlined, 
  ClockCircleOutlined,
  FireOutlined,
  UserOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useAuth } from './AuthContext'
import { userApi, newsApi } from '../services/api'

interface NewsItem {
  id: string
  title: string
  summary: string
  url: string
  source: string
  category: string
  published_at: string
  image_url?: string
  sentiment?: string
}

interface PersonalizedNewsProps {
  limit?: number
  showHeader?: boolean
}

const PersonalizedNews: React.FC<PersonalizedNewsProps> = ({ 
  limit = 10, 
  showHeader = true 
}) => {
  const { user, isAuthenticated } = useAuth()
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(false)
  const [trendingTopics, setTrendingTopics] = useState<string[]>([])
  const [recommendedKeywords, setRecommendedKeywords] = useState<string[]>([])

  useEffect(() => {
    if (isAuthenticated) {
      loadPersonalizedNews()
      loadTrendingTopics()
      loadRecommendedKeywords()
    }
  }, [isAuthenticated])

  // 加载个性化新闻
  const loadPersonalizedNews = async () => {
    setLoading(true)
    try {
      // 获取个性化查询参数
      const queryResponse = await userApi.getUserPersonalizationQuery()
      const queryParams = queryResponse.data.data

      // 使用个性化参数搜索新闻
      const newsResponse = await newsApi.searchNews({
        query: queryParams.keywords?.join(' ') || '',
        categories: queryParams.categories,
        sources: queryParams.sources,
        limit: limit
      })

      if (newsResponse.data.status === 'success') {
        setNews(newsResponse.data.data.articles || [])
      }
    } catch (error: any) {
      console.error('加载个性化新闻失败:', error)
      message.error('加载个性化新闻失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载热门话题
  const loadTrendingTopics = async () => {
    try {
      const response = await userApi.getTrendingTopics()
      if (response.data.status === 'success') {
        setTrendingTopics(response.data.data)
      }
    } catch (error) {
      console.error('加载热门话题失败:', error)
    }
  }

  // 加载推荐关键词
  const loadRecommendedKeywords = async () => {
    try {
      const response = await userApi.getRecommendedKeywords()
      if (response.data.status === 'success') {
        setRecommendedKeywords(response.data.data)
      }
    } catch (error) {
      console.error('加载推荐关键词失败:', error)
    }
  }

  // 记录用户交互
  const recordInteraction = async (type: string, contentId: string, metadata?: any) => {
    try {
      await userApi.recordUserInteraction({
        type,
        content_id: contentId,
        metadata
      })
    } catch (error) {
      console.error('记录用户交互失败:', error)
    }
  }

  // 处理新闻点击
  const handleNewsClick = (item: NewsItem) => {
    // 记录查看行为
    recordInteraction('view', item.id, {
      title: item.title,
      category: item.category,
      source: item.source
    })

    // 打开新闻链接
    window.open(item.url, '_blank')
  }

  // 处理点赞
  const handleLike = (item: NewsItem) => {
    recordInteraction('like', item.id, {
      title: item.title,
      category: item.category
    })
    message.success('已记录您的喜好')
  }

  // 处理分享
  const handleShare = (item: NewsItem) => {
    recordInteraction('share', item.id, {
      title: item.title,
      category: item.category
    })
    
    // 复制链接到剪贴板
    navigator.clipboard.writeText(item.url).then(() => {
      message.success('链接已复制到剪贴板')
    })
  }

  // 处理话题点击
  const handleTopicClick = (topic: string) => {
    recordInteraction('search', `topic_${topic}`, {
      query: topic,
      source: 'trending_topics'
    })
    // 这里可以触发新闻搜索
    message.info(`搜索话题: ${topic}`)
  }

  // 获取情感标签颜色
  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return 'green'
      case 'negative': return 'red'
      case 'neutral': return 'blue'
      default: return 'default'
    }
  }

  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    
    if (hours < 1) return '刚刚'
    if (hours < 24) return `${hours}小时前`
    return date.toLocaleDateString()
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <Empty
          image={<UserOutlined style={{ fontSize: 64, color: '#ccc' }} />}
          description="请登录以查看个性化推荐"
        />
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* 热门话题 */}
      {showHeader && trendingTopics.length > 0 && (
        <Card 
          title={
            <Space>
              <FireOutlined className="text-red-500" />
              <span>热门话题</span>
            </Space>
          }
          size="small"
        >
          <Space wrap>
            {trendingTopics.map((topic, index) => (
              <Tag
                key={topic}
                color={index < 3 ? 'red' : 'blue'}
                className="cursor-pointer hover:opacity-80"
                onClick={() => handleTopicClick(topic)}
              >
                {index < 3 && <FireOutlined />} {topic}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      {/* 推荐关键词 */}
      {showHeader && recommendedKeywords.length > 0 && (
        <Card 
          title="为您推荐"
          size="small"
        >
          <Space wrap>
            {recommendedKeywords.map(keyword => (
              <Tag
                key={keyword}
                color="purple"
                className="cursor-pointer hover:opacity-80"
                onClick={() => handleTopicClick(keyword)}
              >
                {keyword}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      {/* 个性化新闻列表 */}
      <Card 
        title={
          <Space>
            <UserOutlined />
            <span>为您推荐</span>
            <Badge count={news.length} showZero color="blue" />
          </Space>
        }
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadPersonalizedNews}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        }
      >
        <List
          loading={loading}
          dataSource={news}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Tooltip title="喜欢">
                  <Button 
                    type="text" 
                    icon={<HeartOutlined />} 
                    onClick={() => handleLike(item)}
                    size="small"
                  />
                </Tooltip>,
                <Tooltip title="分享">
                  <Button 
                    type="text" 
                    icon={<ShareAltOutlined />} 
                    onClick={() => handleShare(item)}
                    size="small"
                  />
                </Tooltip>,
                <Tooltip title="查看">
                  <Button 
                    type="text" 
                    icon={<EyeOutlined />} 
                    onClick={() => handleNewsClick(item)}
                    size="small"
                  />
                </Tooltip>
              ]}
            >
              <List.Item.Meta
                title={
                  <div className="cursor-pointer hover:text-blue-600" onClick={() => handleNewsClick(item)}>
                    {item.title}
                  </div>
                }
                description={
                  <div className="space-y-2">
                    <p className="text-gray-600 line-clamp-2">{item.summary}</p>
                    <Space wrap>
                      <Tag color="blue">{item.source}</Tag>
                      <Tag color="green">{item.category}</Tag>
                      {item.sentiment && (
                        <Tag color={getSentimentColor(item.sentiment)}>
                          {item.sentiment === 'positive' ? '正面' : 
                           item.sentiment === 'negative' ? '负面' : '中性'}
                        </Tag>
                      )}
                      <Space size="small" className="text-gray-400">
                        <ClockCircleOutlined />
                        <span>{formatTime(item.published_at)}</span>
                      </Space>
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
          locale={{
            emptyText: (
              <Empty
                description="暂无个性化推荐"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )
          }}
        />
      </Card>
    </div>
  )
}

export default PersonalizedNews
