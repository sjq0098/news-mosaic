import React from 'react'
import { Card, Button, Empty, Tag } from 'antd'
import { ClockCircleOutlined, MessageOutlined, FileTextOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { useSearchHistory } from '../hooks/useSearchHistory'

interface RecentSearchCardsProps {
  onHistoryRestore?: (historyItem: any) => void
  maxItems?: number
}

const RecentSearchCards: React.FC<RecentSearchCardsProps> = ({
  onHistoryRestore,
  maxItems = 5
}) => {
  const { searchHistory } = useSearchHistory()

  // 获取最近的搜索记录，优先显示有完整结果的
  const recentSearches = searchHistory
    .filter(item => item.searchResult) // 只显示有完整结果的搜索
    .slice(0, maxItems)

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffHours < 1) return '刚刚'
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`
    
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    })
  }

  const handleRestoreSearch = (historyItem: any) => {
    if (onHistoryRestore) {
      onHistoryRestore(historyItem)
    }
  }

  if (recentSearches.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <span style={{ color: '#718096' }}>暂无可恢复的搜索历史</span>
        }
        style={{ padding: '40px 20px' }}
      />
    )
  }

  return (
    <div className="recent-searches-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
      {recentSearches.map((item) => (
        <div
          key={item.id}
          className="recent-search-card"
          style={{
            background: 'rgba(255, 255, 255, 0.6)',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.4)',
            padding: '16px',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            cursor: 'pointer',
            position: 'relative'
          }}
          onClick={() => handleRestoreSearch(item)}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-3px)'
            e.currentTarget.style.boxShadow = '0 8px 25px rgba(168, 216, 240, 0.25)'
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = 'none'
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.6)'
          }}
        >
          {/* 卡片头部 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <h4 style={{ 
                color: '#2D3748', 
                fontWeight: '600', 
                fontSize: '14px', 
                margin: '0 0 4px 0',
                lineHeight: '1.4',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {item.query}
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <ClockCircleOutlined style={{ color: '#718096', fontSize: '12px' }} />
                <span style={{ color: '#718096', fontSize: '12px' }}>
                  {formatTime(item.timestamp)}
                </span>
              </div>
            </div>
            <div style={{ 
              background: 'linear-gradient(45deg, #10B981, #34D399)',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginLeft: '8px'
            }}>
              <PlayCircleOutlined style={{ color: 'white', fontSize: '12px' }} />
            </div>
          </div>

          {/* 搜索结果摘要 */}
          {item.searchResult && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
                <div style={{ 
                  background: 'rgba(59, 130, 246, 0.1)',
                  color: '#3B82F6',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <FileTextOutlined />
                  {item.searchResult.total_found || 0} 条新闻
                </div>
                <div style={{ 
                  background: 'rgba(16, 185, 129, 0.1)',
                  color: '#10B981',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontWeight: '600'
                }}>
                  {item.searchResult.cards_generated || 0} 张卡片
                </div>
              </div>
              
              {/* 显示对话数量 */}
              {item.chatMessages && item.chatMessages.length > 0 && (
                <div style={{ 
                  background: 'rgba(124, 58, 237, 0.1)',
                  color: '#7C3AED',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontWeight: '600',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <MessageOutlined />
                  {item.chatMessages.length} 条对话记录
                </div>
              )}
            </div>
          )}

          {/* AI摘要预览 */}
          {item.searchResult?.ai_summary && (
            <div style={{ 
              background: 'rgba(215, 240, 233, 0.3)',
              padding: '8px',
              borderRadius: '8px',
              borderLeft: '2px solid #10B981',
              marginBottom: '8px'
            }}>
              <div style={{ 
                fontSize: '12px', 
                color: '#065F46', 
                lineHeight: '1.4',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical'
              }}>
                {item.searchResult.ai_summary.substring(0, 80)}...
              </div>
            </div>
          )}

          {/* 恢复按钮 */}
          <div style={{ textAlign: 'center', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.5)' }}>
            <span style={{ 
              color: '#10B981', 
              fontSize: '12px', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px'
            }}>
              <PlayCircleOutlined />
              点击恢复完整分析
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default RecentSearchCards