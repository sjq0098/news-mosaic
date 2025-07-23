import React, { useState } from 'react'
import { List, Button, Tooltip, Empty, Spin, Modal, message } from 'antd'
import {
  HistoryOutlined,
  SearchOutlined,
  DeleteOutlined,
  ClearOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  MessageOutlined
} from '@ant-design/icons'
import { useSearchHistory, SearchHistoryItem } from '../hooks/useSearchHistory'

interface SearchHistoryProps {
  onSearchSelect?: (query: string) => void
  onHistoryRestore?: (historyItem: SearchHistoryItem) => void
  className?: string
  maxHeight?: string
}

const SearchHistory: React.FC<SearchHistoryProps> = ({
  onSearchSelect,
  onHistoryRestore,
  className = '',
  maxHeight = '300px'
}) => {
  const {
    searchHistory,
    loading,
    deleteSearchRecord,
    clearSearchHistory
  } = useSearchHistory()

  const [deleteLoading, setDeleteLoading] = useState<string | null>(null)

  // 处理历史记录选择
  const handleHistorySelect = (historyItem: SearchHistoryItem) => {
    if (historyItem.searchResult && onHistoryRestore) {
      // 如果有保存的搜索结果，恢复完整状态
      onHistoryRestore(historyItem)
    } else if (onSearchSelect) {
      // 如果没有保存的结果，重新搜索
      onSearchSelect(historyItem.query)
    }
  }

  // 处理删除单条记录
  const handleDeleteRecord = async (e: React.MouseEvent, recordId: string) => {
    e.stopPropagation()
    setDeleteLoading(recordId)
    try {
      await deleteSearchRecord(recordId)
      message.success('搜索记录已删除')
    } catch (error) {
      message.error('删除失败')
    } finally {
      setDeleteLoading(null)
    }
  }

  // 处理清空历史
  const handleClearHistory = () => {
    Modal.confirm({
      title: '确认清空搜索历史',
      icon: <ExclamationCircleOutlined />,
      content: '此操作将清空所有搜索历史记录，且无法恢复。确定要继续吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await clearSearchHistory()
        } catch (error) {
          message.error('清空失败')
        }
      }
    })
  }

  // 格式化时间显示
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`
    
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className={`search-history-container ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Spin size="small" />
          <span className="ml-2 text-white/60 text-sm">加载搜索历史...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`search-history-container ${className}`}>
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-2">
          <HistoryOutlined className="text-white/70 text-sm" />
          <span className="text-white/90 text-sm font-medium">搜索历史</span>
        </div>
        {searchHistory.length > 0 && (
          <Tooltip title="清空历史">
            <Button
              type="text"
              size="small"
              icon={<ClearOutlined />}
              onClick={handleClearHistory}
              className="text-white/50 hover:text-white/80 hover:bg-white/10 border-none"
            />
          </Tooltip>
        )}
      </div>

      {/* 历史记录列表 */}
      <div 
        className="search-history-list custom-scrollbar"
        style={{ maxHeight }}
      >
        {searchHistory.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span className="text-white/50 text-sm">暂无搜索历史</span>
            }
            className="py-4"
          />
        ) : (
          <List
            size="small"
            dataSource={searchHistory}
            renderItem={(item: SearchHistoryItem) => (
              <List.Item
                key={item.id}
                className="search-history-item group cursor-pointer transition-all duration-300"
                onClick={() => handleHistorySelect(item)}
                style={{
                  border: 'none',
                  padding: '16px 12px',
                  borderRadius: '16px',
                  marginBottom: '8px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  minHeight: '72px'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.25)'
                  e.currentTarget.style.transform = 'translateX(6px) scale(1.02)'
                  e.currentTarget.style.boxShadow = '0 8px 25px rgba(168, 216, 240, 0.3)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
                  e.currentTarget.style.transform = 'translateX(0) scale(1)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      {item.searchResult ? (
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-md">
                          <FileTextOutlined className="text-white text-sm" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-md">
                          <SearchOutlined className="text-white text-sm" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-gray-800 text-sm truncate font-semibold leading-tight">
                        {item.query}
                      </div>
                      <div className="flex items-center space-x-3 mt-1">
                        <div className="flex items-center space-x-1">
                          <ClockCircleOutlined className="text-gray-500 text-xs" />
                          <span className="text-gray-500 text-xs font-medium">
                            {formatTime(item.timestamp)}
                          </span>
                        </div>
                        {item.searchResult && (
                          <div className="flex items-center space-x-1">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-green-600 text-xs font-medium">
                              完整结果已保存
                            </span>
                          </div>
                        )}
                        {item.chatMessages && item.chatMessages.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <MessageOutlined className="text-purple-500 text-xs" />
                            <span className="text-purple-500 text-xs font-medium">
                              {item.chatMessages.length} 条对话
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex-shrink-0 ml-2">
                    <Tooltip title="删除此记录" placement="left">
                      <Button
                        type="text"
                        size="small"
                        icon={<DeleteOutlined />}
                        loading={deleteLoading === item.id}
                        onClick={(e) => handleDeleteRecord(e, item.id)}
                        className="opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
                        style={{
                          border: 'none',
                          background: 'rgba(239, 68, 68, 0.1)',
                          color: '#EF4444',
                          borderRadius: '12px',
                          width: '32px',
                          height: '32px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'
                          e.currentTarget.style.transform = 'scale(1.1)'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'
                          e.currentTarget.style.transform = 'scale(1)'
                        }}
                      />
                    </Tooltip>
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}
      </div>

      <style jsx>{`
        .search-history-container {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 16px;
          padding: 16px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(15px);
          -webkit-backdrop-filter: blur(15px);
        }

        .search-history-list {
          overflow-y: auto;
        }

        .search-history-item {
          border: none !important;
          padding: 12px 8px !important;
          border-radius: 12px !important;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .search-history-item:hover {
          background: rgba(255, 255, 255, 0.2) !important;
          transform: translateX(4px) !important;
          box-shadow: 0 4px 12px rgba(168, 216, 240, 0.15) !important;
        }

        /* 马卡农配色文本 */
        .search-history-item .text-white\\/90 {
          color: #2D3748 !important;
          font-weight: 600 !important;
        }

        .search-history-item .text-white\\/40 {
          color: #718096 !important;
        }

        .search-history-item .text-white\\/70 {
          color: #4A5568 !important;
        }

        .search-history-item .text-white\\/50 {
          color: #718096 !important;
        }

        .search-history-item .text-green-400 {
          color: #10B981 !important;
        }

        /* 图标颜色调整 */
        .search-history-container .anticon {
          color: #4A5568 !important;
        }

        .search-history-container .text-white\\/70 {
          color: #4A5568 !important;
        }

        .search-history-container .text-white\\/90 {
          color: #2D3748 !important;
        }

        .search-history-container .text-white\\/50 {
          color: #718096 !important;
        }

        /* 按钮样式 */
        .search-history-container .ant-btn {
          border-radius: 10px !important;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .search-history-container .ant-btn:hover {
          background: rgba(255, 255, 255, 0.3) !important;
          transform: translateY(-1px) !important;
          box-shadow: 0 4px 8px rgba(168, 216, 240, 0.2) !important;
        }

        /* 空状态样式 */
        .search-history-container .ant-empty-description {
          color: #718096 !important;
        }

        /* 自定义滚动条 - 马卡农风格 */
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(135deg, var(--macaron-mint), var(--macaron-yellow));
          border-radius: 3px;
          transition: background 0.3s ease;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(135deg, var(--macaron-pink), var(--macaron-lavender));
        }

        /* 加载状态样式 */
        .search-history-container .ant-spin {
          color: #4A5568 !important;
        }

        /* 删除按钮特殊样式 */
        .search-history-item .hover\\:text-red-400:hover {
          color: #EF4444 !important;
          background: rgba(239, 68, 68, 0.1) !important;
        }

        /* 悬停动画增强 */
        .search-history-item {
          position: relative;
          overflow: hidden;
        }

        .search-history-item::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
          transition: left 0.5s;
        }

        .search-history-item:hover::before {
          left: 100%;
        }
      `}</style>
    </div>
  )
}

export default SearchHistory
