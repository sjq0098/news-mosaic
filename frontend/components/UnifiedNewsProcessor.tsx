import React, { useState, useEffect, useImperativeHandle, forwardRef, useCallback } from 'react'
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
  ExclamationCircleOutlined,
  MessageOutlined
} from '@ant-design/icons'
import { newsPipelineApi, enhancedChatApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useSearchHistory } from '../hooks/useSearchHistory'
import MarkdownRenderer from './MarkdownRenderer'

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

interface UnifiedNewsProcessorProps {
  externalQuery?: string
  onQueryChange?: (query: string) => void
}

export interface UnifiedNewsProcessorRef {
  triggerSearch: (query: string) => void
  restoreHistoryState: (historyItem: any) => void
  clearCurrentSession: () => Promise<void>
}

const UnifiedNewsProcessor = forwardRef<UnifiedNewsProcessorRef, UnifiedNewsProcessorProps>(
  ({ externalQuery, onQueryChange }, ref) => {
    const { user } = useAuth()
    const { addSearchRecord } = useSearchHistory()
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<NewsProcessingResult | null>(null)
    const [chatLoading, setChatLoading] = useState(false)
    const [chatMessages, setChatMessages] = useState<any[]>([])
    const [currentSessionId, setCurrentSessionId] = useState<string>('')
    const [currentQuery, setCurrentQuery] = useState('')
  
  // 处理配置
  const [config, setConfig] = useState({
    num_results: 10,
    enable_storage: true,
    enable_vectorization: true, // 启用向量化以支持智能对话
    enable_ai_analysis: true,
    enable_card_generation: true,
    enable_sentiment_analysis: true,
    enable_user_memory: true, // 启用用户记忆以支持个性化对话
    max_cards: 5,
    personalization_level: 0.5
  })

  const handleNewsProcessing = async (query: string) => {
    if (!query.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    setCurrentQuery(query)

    try {
      const response = await newsPipelineApi.processNews({
        query,
        ...config
      })

      if (response.data.success) {
        setResult(response.data)
        message.success('新闻处理完成！')

        // 记录搜索历史，包含完整的搜索结果和对话记录
        await addSearchRecord(
          query,
          {
            results_count: response.data.stages?.find((s: any) => s.stage === 'news_collection')?.data?.length || 0,
            cards_generated: response.data.stages?.find((s: any) => s.stage === 'card_generation')?.data?.length || 0
          },
          response.data, // 保存完整的搜索结果
          chatMessages, // 保存当前的对话记录
          currentSessionId // 保存会话ID
        )

        // 通知父组件查询变化
        if (onQueryChange) {
          onQueryChange(query)
        }
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

  // 恢复历史状态
  const restoreHistoryState = useCallback((historyItem: any) => {
    if (historyItem.searchResult) {
      setResult(historyItem.searchResult)
      setCurrentQuery(historyItem.query)

      if (historyItem.chatMessages) {
        setChatMessages(historyItem.chatMessages)
      }

      if (historyItem.sessionId) {
        setCurrentSessionId(historyItem.sessionId)
      }

      message.success(`已恢复搜索结果: ${historyItem.query}`)
    }
  }, [])

  // 清空当前会话状态
  const clearCurrentSession = useCallback(async () => {
    // 如果有当前搜索结果和查询，先保存到历史记录（包含最新的对话记录）
    if (result && currentQuery) {
      try {
        await addSearchRecord(
          currentQuery,
          {
            results_count: result.total_found || 0,
            cards_generated: result.cards_generated || 0
          },
          result, // 保存完整的搜索结果
          chatMessages, // 保存当前的对话记录（包含用户的对话）
          currentSessionId // 保存会话ID
        )
      } catch (error) {
        console.error('保存搜索历史失败:', error)
      }
    }

    // 清空所有状态
    setResult(null)
    setChatMessages([])
    setCurrentSessionId('')
    setCurrentQuery('')
    setLoading(false)
    setChatLoading(false)
    message.success('已开启新的搜索会话')
  }, [result, currentQuery, chatMessages, currentSessionId, addSearchRecord])

  // 暴露给父组件的方法
  useImperativeHandle(ref, () => ({
    triggerSearch: (query: string) => {
      setCurrentQuery(query)
      handleNewsProcessing(query)
    },
    restoreHistoryState,
    clearCurrentSession
  }))

  // 监听外部查询变化
  useEffect(() => {
    if (externalQuery && externalQuery !== currentQuery) {
      handleNewsProcessing(externalQuery)
    }
  }, [externalQuery])

  const handleChatWithNews = async (userMessage: string) => {
    if (!userMessage.trim()) {
      message.warning('请输入问题')
      return
    }

    setChatLoading(true)
    try {
      const response = await enhancedChatApi.chatWithRAG({
        user_id: user?.id || user?.username || 'anonymous',
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

        const updatedMessages = [...chatMessages, newMessage, aiResponse]
        setChatMessages(updatedMessages)
        setCurrentSessionId(response.data.session_id)

        // 对话后更新搜索历史记录（包含最新的对话）
        if (result && currentQuery) {
          try {
            await addSearchRecord(
              currentQuery,
              {
                results_count: result.total_found || 0,
                cards_generated: result.cards_generated || 0
              },
              result, // 保存完整的搜索结果
              updatedMessages, // 保存包含最新对话的记录
              response.data.session_id // 保存会话ID
            )
          } catch (error) {
            console.error('更新搜索历史失败:', error)
          }
        }
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
            dot={stage.success ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
          >
            <div>
              <strong>{stageNames[stage.stage as keyof typeof stageNames] || stage.stage}</strong>
              <div style={{ fontSize: '12px', color: '#666' }}>
                耗时: {stage.processing_time.toFixed(2)}s
              </div>
              {stage.error && (
                <Alert message={stage.error} type="error" style={{ marginTop: 4 }} />
              )}
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    )
  }

  const renderStructuredSummary = (summary: string) => {
    // 尝试将AI摘要结构化展示
    const sections = summary.split('\n\n').filter(section => section.trim())

    return (
      <div className="structured-summary">
        {sections.map((section, index) => {
          const lines = section.split('\n').filter(line => line.trim())
          if (lines.length === 0) return null

          const isTitle = lines[0].includes('：') || lines[0].includes(':') || lines[0].length < 20

          return (
            <div key={index} className="summary-section">
              {isTitle && lines.length > 1 ? (
                <>
                  <h4 className="summary-section-title">{lines[0]}</h4>
                  <div className="summary-section-content">
                    {lines.slice(1).map((line, lineIndex) => (
                      <p key={lineIndex} className="summary-line">{line}</p>
                    ))}
                  </div>
                </>
              ) : (
                <div className="summary-section-content">
                  {lines.map((line, lineIndex) => (
                    <p key={lineIndex} className="summary-line">{line}</p>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  const renderSentimentOverview = () => {
    if (!result?.sentiment_overview) return null

    const { sentiment_overview } = result
    return (
      <div className="sentiment-stats">
        <div className="sentiment-stat positive">
          <div className="sentiment-icon">😊</div>
          <div className="sentiment-info">
            <div className="sentiment-percentage">{sentiment_overview.positive?.percentage || 0}%</div>
            <div className="sentiment-label">正面情感</div>
          </div>
        </div>
        <div className="sentiment-stat neutral">
          <div className="sentiment-icon">😐</div>
          <div className="sentiment-info">
            <div className="sentiment-percentage">{sentiment_overview.neutral?.percentage || 0}%</div>
            <div className="sentiment-label">中性情感</div>
          </div>
        </div>
        <div className="sentiment-stat negative">
          <div className="sentiment-icon">😞</div>
          <div className="sentiment-info">
            <div className="sentiment-percentage">{sentiment_overview.negative?.percentage || 0}%</div>
            <div className="sentiment-label">负面情感</div>
          </div>
        </div>
      </div>
    )
  }

  const renderNewsCards = () => {
    if (!result?.news_cards?.length) return null

    return (
      <Row gutter={[24, 24]} className="news-cards-grid">
        {result.news_cards.map((card, index) => (
          <Col xs={24} sm={24} md={12} lg={8} key={index}>
            <div className="news-card">
              <div className="news-card-header">
                <div className="sentiment-indicator">
                  <div className={`sentiment-dot sentiment-${card.metadata?.sentiment_label || 'neutral'}`}></div>
                </div>
                <div className="news-card-meta">
                  <span className="news-source">{card.source}</span>
                  <span className="news-date">{new Date(card.published_at).toLocaleDateString('zh-CN')}</span>
                </div>
              </div>

              <div className="news-card-content">
                <h3 className="news-card-title">{card.title}</h3>
                <p className="news-card-summary">{card.metadata?.summary}</p>

                <div className="news-card-tags">
                  <span className={`sentiment-tag sentiment-${card.metadata?.sentiment_label || 'neutral'}`}>
                    {card.metadata?.sentiment_label === 'positive' ? '😊 正面' :
                     card.metadata?.sentiment_label === 'negative' ? '😞 负面' : '😐 中性'}
                  </span>
                  <span className="importance-tag">
                    ⭐ 重要性 {card.display_priority}/10
                  </span>
                </div>
              </div>

              <div className="news-card-footer">
                <Button
                  type="link"
                  href={card.url}
                  target="_blank"
                  className="read-more-button"
                  icon={<FileTextOutlined />}
                >
                  阅读原文
                </Button>
              </div>
            </div>
          </Col>
        ))}
      </Row>
    )
  }

  const renderChatInterface = () => (
    <div className="chat-interface">
      <div className="chat-messages">
        {chatMessages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="chat-empty-icon">💬</div>
            <h4 className="chat-empty-title">开始智能对话</h4>
            <p className="chat-empty-description">
              您可以询问有关这些新闻的任何问题，例如：
            </p>
            <div className="chat-suggestions">
              <Button
                className="chat-suggestion"
                type="text"
                onClick={() => handleChatWithNews("这些新闻中最重要的事件是什么？")}
              >
                这些新闻中最重要的事件是什么？
              </Button>
              <Button
                className="chat-suggestion"
                type="text"
                onClick={() => handleChatWithNews("总结一下正面和负面的观点")}
              >
                总结一下正面和负面的观点
              </Button>
              <Button
                className="chat-suggestion"
                type="text"
                onClick={() => handleChatWithNews("这些新闻反映了什么趋势？")}
              >
                这些新闻反映了什么趋势？
              </Button>
            </div>
          </div>
        ) : (
          <>
            {chatMessages.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.role === 'user' ? 'user-message' : 'ai-message'}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {msg.role === 'assistant' ? (
                      <MarkdownRenderer content={msg.content} />
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.confidence_score && (
                    <div className="message-meta">
                      <span className="confidence-score">
                        <CheckCircleOutlined /> 置信度: {(msg.confidence_score * 100).toFixed(1)}%
                      </span>
                      <span className="sources-count">
                        <FileTextOutlined /> 来源: {msg.sources_count}条新闻
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="chat-loading">
                <Spin size="small" />
                <span>AI正在思考...</span>
              </div>
            )}
          </>
        )}
      </div>
      <div className="chat-input">
        <Search
          placeholder="询问关于这些新闻的问题..."
          enterButton={
            <Button type="primary" loading={chatLoading}>
              发送
            </Button>
          }
          size="large"
          onSearch={handleChatWithNews}
          disabled={chatLoading}
          className="chat-search-input"
        />
        <div className="chat-input-hint">
          提示：您可以询问特定事件、观点分析、趋势预测等
        </div>
      </div>
    </div>
  )

  return (
    <div style={{ padding: '24px' }}>
      <div className="search-container macaron-search-container">
        <div className="search-header">
          <h2 className="search-title macaron-title">探索新闻洞察</h2>
          <p className="search-subtitle macaron-subtitle">输入关键词，发现最新新闻动态与深度分析</p>
        </div>
        <div className="search-box-container">
          <Search
            placeholder="输入感兴趣的话题，例如：南开大学、人工智能、气候变化..."
            enterButton={
              <Button 
                type="primary" 
                icon={<SearchOutlined />} 
                loading={loading} 
                className="search-button macaron-search-button"
                style={{
                  background: 'linear-gradient(45deg, #D7F0E9, #FFF2CC)',
                  borderColor: 'transparent',
                  color: '#4A5568'
                }}
              >
                智能分析
              </Button>
            }
            size="large"
            onSearch={handleNewsProcessing}
            disabled={loading}
            className="main-search-box macaron-search-box"
            style={{
              borderRadius: '16px'
            }}
          />
          <div className="search-options">
            <Select
              size="small"
              value={config.num_results}
              onChange={(value) => setConfig(prev => ({ ...prev, num_results: value }))}
              className="search-option-select macaron-select"
              style={{
                borderRadius: '12px'
              }}
            >
              <Option value={10}>10 条结果</Option>
              <Option value={20}>20 条结果</Option>
              <Option value={50}>50 条结果</Option>
              <Option value={100}>100 条结果</Option>
            </Select>
            <Select
              size="small"
              value={config.max_cards}
              onChange={(value) => setConfig(prev => ({ ...prev, max_cards: value }))}
              className="search-option-select macaron-select"
              style={{
                borderRadius: '12px'
              }}
            >
              <Option value={3}>3 张卡片</Option>
              <Option value={5}>5 张卡片</Option>
              <Option value={10}>10 张卡片</Option>
            </Select>
            <Button
              size="small"
              type="text"
              onClick={() => document.getElementById('advanced-settings-modal')?.classList.toggle('show')}
              className="advanced-settings-button macaron-text-button"
              style={{
                color: '#4A5568',
                borderRadius: '12px'
              }}
            >
              高级设置
            </Button>
          </div>
        </div>

        {/* 高级设置模态框 - 马卡农风格 */}
        <div id="advanced-settings-modal" className="advanced-settings-modal">
          <Card 
            title="高级处理设置" 
            size="small" 
            extra={<Button type="text" onClick={() => document.getElementById('advanced-settings-modal')?.classList.toggle('show')}>关闭</Button>}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(20px)',
              borderRadius: '20px',
              border: '1px solid rgba(255, 255, 255, 0.5)'
            }}
          >
            <Row gutter={16}>
              <Col span={24}>
                <Space wrap>
                  <span style={{ color: '#4A5568' }}>存储: <Switch size="small" checked={config.enable_storage} onChange={(checked) => setConfig(prev => ({ ...prev, enable_storage: checked }))} /></span>
                  <span style={{ color: '#4A5568' }}>向量化: <Switch size="small" checked={config.enable_vectorization} onChange={(checked) => setConfig(prev => ({ ...prev, enable_vectorization: checked }))} /></span>
                  <span style={{ color: '#4A5568' }}>AI分析: <Switch size="small" checked={config.enable_ai_analysis} onChange={(checked) => setConfig(prev => ({ ...prev, enable_ai_analysis: checked }))} /></span>
                  <span style={{ color: '#4A5568' }}>卡片生成: <Switch size="small" checked={config.enable_card_generation} onChange={(checked) => setConfig(prev => ({ ...prev, enable_card_generation: checked }))} /></span>
                </Space>
              </Col>
            </Row>
          </Card>
        </div>
      </div>

      {/* 处理结果 */}
      {result && (
        <div className="results-container macaron-results">
          {/* 处理概览 - 马卡农风格 */}
          <div 
            className="processing-overview"
            style={{
              background: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              padding: '24px',
              marginBottom: '24px'
            }}
          >
            <div className="overview-stats">
              <div className="stat-item macaron-stat">
                <div className="stat-icon" style={{ background: 'linear-gradient(45deg, #FADADD, #FFF2CC)', borderRadius: '16px', padding: '12px' }}>📰</div>
                <div className="stat-content">
                  <div className="stat-value" style={{ color: '#4A5568' }}>{result.total_found}</div>
                  <div className="stat-label" style={{ color: '#718096' }}>篇相关新闻</div>
                </div>
              </div>
              <div className="stat-item macaron-stat">
                <div className="stat-icon" style={{ background: 'linear-gradient(45deg, #D7F0E9, #E8D5FF)', borderRadius: '16px', padding: '12px' }}>🎯</div>
                <div className="stat-content">
                  <div className="stat-value" style={{ color: '#4A5568' }}>{result.cards_generated}</div>
                  <div className="stat-label" style={{ color: '#718096' }}>张核心事件卡片</div>
                </div>
              </div>
              <div className="stat-item macaron-stat">
                <div className="stat-icon" style={{ background: 'linear-gradient(45deg, #FFF2CC, #FADADD)', borderRadius: '16px', padding: '12px' }}>⚡</div>
                <div className="stat-content">
                  <div className="stat-value" style={{ color: '#4A5568' }}>{result.processing_time.toFixed(1)}s</div>
                  <div className="stat-label" style={{ color: '#718096' }}>处理完成</div>
                </div>
              </div>
            </div>
          </div>

          {/* AI分析摘要 - 马卡农风格 */}
          {result.ai_summary && (
            <div 
              className="ai-analysis-section"
              style={{
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(20px)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 0.5)',
                padding: '24px',
                marginBottom: '24px'
              }}
            >
              <h3 className="section-title" style={{ color: '#4A5568', marginBottom: '16px' }}>
                <RobotOutlined className="section-icon" style={{ color: '#D7F0E9' }} />
                智能分析洞察
              </h3>
              <div className="ai-summary-content">
                {renderStructuredSummary(result.ai_summary)}
              </div>
            </div>
          )}

          {/* 情感分析概览 - 马卡农风格 */}
          {result.sentiment_overview && (
            <div 
              className="sentiment-section"
              style={{
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(20px)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 0.5)',
                padding: '24px',
                marginBottom: '24px'
              }}
            >
              <h3 className="section-title" style={{ color: '#4A5568', marginBottom: '16px' }}>
                <HeartOutlined className="section-icon" style={{ color: '#FADADD' }} />
                情感倾向分析
              </h3>
              <div className="sentiment-overview">
                {renderSentimentOverview()}
              </div>
            </div>
          )}

          {/* 新闻卡片 - 马卡农风格 */}
          <div 
            className="news-cards-section"
            style={{
              background: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              padding: '24px',
              marginBottom: '24px'
            }}
          >
            <h3 className="section-title" style={{ color: '#4A5568', marginBottom: '16px' }}>
              <FileTextOutlined className="section-icon" style={{ color: '#FFF2CC' }} />
              核心新闻事件
            </h3>
            {renderNewsCards()}
          </div>

          {/* 智能对话区域 - 马卡农风格 */}
          <div 
            className="chat-section"
            style={{
              background: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              padding: '24px'
            }}
          >
            <h3 className="section-title" style={{ color: '#4A5568', marginBottom: '16px' }}>
              <MessageOutlined className="section-icon" style={{ color: '#E8D5FF' }} />
              继续深入探讨
            </h3>
            <div className="chat-container">
              {renderChatInterface()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

UnifiedNewsProcessor.displayName = 'UnifiedNewsProcessor'

export default UnifiedNewsProcessor
