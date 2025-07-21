import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Input, 
  Button, 
  Space, 
  Spin, 
  Alert, 
  Tabs, 
  Tag, 
  Progress, 
  Timeline,
  Statistic,
  Row,
  Col,
  message,
  Switch,
  Slider,
  Select
} from 'antd'
import { 
  SearchOutlined, 
  RobotOutlined, 
  HeartOutlined, 
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { newsPipelineApi, enhancedChatApi } from '../services/api'

const { Search } = Input
const { TabPane } = Tabs
const { Option } = Select

interface ProcessingStage {
  stage: string
  success: boolean
  data?: any
  error?: string
  processing_time: number
}

interface NewsProcessingResult {
  success: boolean
  message: string
  pipeline_id: string
  query: string
  total_found: number
  processed_count: number
  cards_generated: number
  vectors_created: number
  news_articles: any[]
  news_cards: any[]
  ai_summary?: string
  sentiment_overview?: any
  processing_time: number
  stage_results: ProcessingStage[]
  warnings: string[]
  errors: string[]
  user_interests_updated: boolean
  recommended_queries: string[]
}

const UnifiedNewsProcessor: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<NewsProcessingResult | null>(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [chatMessages, setChatMessages] = useState<any[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  
  // 处理配置
  const [config, setConfig] = useState({
    num_results: 10,
    enable_storage: true,
    enable_vectorization: false, // 默认关闭向量化（耗时）
    enable_ai_analysis: true,
    enable_card_generation: true,
    enable_sentiment_analysis: true,
    enable_user_memory: false, // 默认关闭用户记忆（耗时）
    max_cards: 5,
    personalization_level: 0.5
  })

  const handleNewsProcessing = async (query: string) => {
    if (!query.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    try {
      const response = await newsPipelineApi.processNews({
        query,
        ...config
      })

      if (response.data.success) {
        setResult(response.data)
        message.success('新闻处理完成！')
      } else {
        message.error(response.data.message || '处理失败')
      }
    } catch (error) {
      console.error('News processing error:', error)
      message.error('新闻处理失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleChatWithNews = async (userMessage: string) => {
    if (!userMessage.trim()) {
      message.warning('请输入问题')
      return
    }

    setChatLoading(true)
    try {
      const response = await enhancedChatApi.chatWithRAG({
        user_id: 'anonymous', // 添加必需的user_id参数
        message: userMessage,
        session_id: currentSessionId,
        max_context_news: 5,
        use_user_memory: true,
        enable_personalization: true
      })

      if (response.data.success) {
        const newMessage = {
          role: 'user',
          content: userMessage,
          timestamp: new Date()
        }
        const aiResponse = {
          role: 'assistant',
          content: response.data.ai_response,
          timestamp: new Date(),
          confidence_score: response.data.confidence_score,
          sources_count: response.data.sources_count,
          relevant_news: response.data.relevant_news
        }

        setChatMessages(prev => [...prev, newMessage, aiResponse])
        setCurrentSessionId(response.data.session_id)
      } else {
        message.error('对话失败')
      }
    } catch (error) {
      console.error('Chat error:', error)
      message.error('对话失败，请稍后重试')
    } finally {
      setChatLoading(false)
    }
  }

  const renderProcessingStages = () => {
    if (!result?.stage_results) return null

    const stageNames = {
      search: '新闻搜索',
      storage: '数据存储',
      vectorization: '向量化处理',
      ai_analysis: 'AI分析',
      card_generation: '卡片生成',
      sentiment_analysis: '情感分析',
      user_memory_update: '用户记忆更新'
    }

    return (
      <Timeline>
        {result.stage_results.map((stage, index) => (
          <Timeline.Item
            key={index}
            color={stage.success ? 'green' : 'red'}
            icon={stage.success ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
          >
            <div>
              <strong>{stageNames[stage.stage] || stage.stage}</strong>
              <div style={{ fontSize: '12px', color: '#666' }}>
                耗时: {stage.processing_time.toFixed(2)}s
              </div>
              {stage.error && (
                <Alert message={stage.error} type="error" size="small" style={{ marginTop: 4 }} />
              )}
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    )
  }

  const renderSentimentOverview = () => {
    if (!result?.sentiment_overview) return null

    const { sentiment_overview } = result
    return (
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="正面情感"
            value={sentiment_overview.positive?.percentage || 0}
            suffix="%"
            valueStyle={{ color: '#3f8600' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="中性情感"
            value={sentiment_overview.neutral?.percentage || 0}
            suffix="%"
            valueStyle={{ color: '#666' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="负面情感"
            value={sentiment_overview.negative?.percentage || 0}
            suffix="%"
            valueStyle={{ color: '#cf1322' }}
          />
        </Col>
      </Row>
    )
  }

  const renderNewsCards = () => {
    if (!result?.news_cards?.length) return null

    return (
      <Row gutter={[16, 16]}>
        {result.news_cards.map((card, index) => (
          <Col span={24} key={index}>
            <Card
              size="small"
              title={card.title}
              extra={<Tag color="blue">{card.source}</Tag>}
            >
              <p>{card.metadata?.summary}</p>
              <Space>
                <Tag color={card.metadata?.sentiment_label === 'positive' ? 'green' : 
                           card.metadata?.sentiment_label === 'negative' ? 'red' : 'default'}>
                  {card.metadata?.sentiment_label || '中性'}
                </Tag>
                <Tag>重要性: {card.display_priority}/10</Tag>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    )
  }

  const renderChatInterface = () => (
    <div style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', border: '1px solid #d9d9d9', borderRadius: '6px' }}>
        {chatMessages.map((msg, index) => (
          <div key={index} style={{ marginBottom: '16px' }}>
            <div style={{ 
              background: msg.role === 'user' ? '#1890ff' : '#f0f0f0',
              color: msg.role === 'user' ? 'white' : 'black',
              padding: '8px 12px',
              borderRadius: '8px',
              maxWidth: '80%',
              marginLeft: msg.role === 'user' ? 'auto' : '0',
              marginRight: msg.role === 'user' ? '0' : 'auto'
            }}>
              {msg.content}
              {msg.confidence_score && (
                <div style={{ fontSize: '12px', marginTop: '4px', opacity: 0.8 }}>
                  置信度: {(msg.confidence_score * 100).toFixed(1)}% | 来源: {msg.sources_count}条新闻
                </div>
              )}
            </div>
          </div>
        ))}
        {chatLoading && (
          <div style={{ textAlign: 'center' }}>
            <Spin size="small" /> AI正在思考...
          </div>
        )}
      </div>
      <div style={{ marginTop: '16px' }}>
        <Search
          placeholder="询问关于新闻的问题..."
          enterButton="发送"
          size="large"
          onSearch={handleChatWithNews}
          loading={chatLoading}
        />
      </div>
    </div>
  )

  return (
    <div style={{ padding: '24px' }}>
      <Card title="统一新闻处理系统" style={{ marginBottom: '24px' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 搜索区域 */}
          <div>
            <Search
              placeholder="输入新闻搜索关键词..."
              enterButton={
                <Button type="primary" icon={<SearchOutlined />} loading={loading}>
                  智能处理
                </Button>
              }
              size="large"
              onSearch={handleNewsProcessing}
              disabled={loading}
            />
          </div>

          {/* 配置选项 */}
          <Card title="处理配置" size="small">
            <Row gutter={16}>
              <Col span={6}>
                <div>结果数量: {config.num_results}</div>
                <Slider
                  min={5}
                  max={50}
                  value={config.num_results}
                  onChange={(value) => setConfig(prev => ({ ...prev, num_results: value }))}
                />
              </Col>
              <Col span={6}>
                <div>最大卡片: {config.max_cards}</div>
                <Slider
                  min={1}
                  max={20}
                  value={config.max_cards}
                  onChange={(value) => setConfig(prev => ({ ...prev, max_cards: value }))}
                />
              </Col>
              <Col span={12}>
                <Space wrap>
                  <span>存储: <Switch size="small" checked={config.enable_storage} onChange={(checked) => setConfig(prev => ({ ...prev, enable_storage: checked }))} /></span>
                  <span>向量化: <Switch size="small" checked={config.enable_vectorization} onChange={(checked) => setConfig(prev => ({ ...prev, enable_vectorization: checked }))} /></span>
                  <span>AI分析: <Switch size="small" checked={config.enable_ai_analysis} onChange={(checked) => setConfig(prev => ({ ...prev, enable_ai_analysis: checked }))} /></span>
                  <span>卡片生成: <Switch size="small" checked={config.enable_card_generation} onChange={(checked) => setConfig(prev => ({ ...prev, enable_card_generation: checked }))} /></span>
                </Space>
              </Col>
            </Row>
          </Card>
        </Space>
      </Card>

      {/* 处理结果 */}
      {result && (
        <Tabs defaultActiveKey="overview">
          <TabPane tab={<span><FileTextOutlined />处理概览</span>} key="overview">
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={6}>
                <Statistic title="找到新闻" value={result.total_found} />
              </Col>
              <Col span={6}>
                <Statistic title="处理数量" value={result.processed_count} />
              </Col>
              <Col span={6}>
                <Statistic title="生成卡片" value={result.cards_generated} />
              </Col>
              <Col span={6}>
                <Statistic title="处理时间" value={result.processing_time.toFixed(2)} suffix="s" />
              </Col>
            </Row>
            
            {result.ai_summary && (
              <Card title="AI分析摘要" style={{ marginBottom: '16px' }}>
                <p>{result.ai_summary}</p>
              </Card>
            )}
          </TabPane>

          <TabPane tab={<span><ClockCircleOutlined />处理流程</span>} key="stages">
            {renderProcessingStages()}
          </TabPane>

          <TabPane tab={<span><HeartOutlined />情感分析</span>} key="sentiment">
            {renderSentimentOverview()}
          </TabPane>

          <TabPane tab={<span><FileTextOutlined />新闻卡片</span>} key="cards">
            {renderNewsCards()}
          </TabPane>

          <TabPane tab={<span><RobotOutlined />智能对话</span>} key="chat">
            {renderChatInterface()}
          </TabPane>
        </Tabs>
      )}
    </div>
  )
}

export default UnifiedNewsProcessor
