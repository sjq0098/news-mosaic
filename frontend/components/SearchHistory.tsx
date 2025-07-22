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
                className="search-history-item group cursor-pointer hover:bg-white/5 rounded-lg px-2 py-1 transition-all duration-200"
                onClick={() => handleHistorySelect(item)}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    {item.searchResult ? (
                      <FileTextOutlined className="text-green-400 text-xs flex-shrink-0" />
                    ) : (
                      <SearchOutlined className="text-white/50 text-xs flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-white/90 text-sm truncate font-medium">
                        {item.query}
                      </div>
                      <div className="flex items-center space-x-2 mt-0.5">
                        <div className="flex items-center space-x-1">
                          <ClockCircleOutlined className="text-white/40 text-xs" />
                          <span className="text-white/40 text-xs">
                            {formatTime(item.timestamp)}
                          </span>
                        </div>
                        {item.searchResult && (
                          <div className="flex items-center space-x-1">
                            <MessageOutlined className="text-green-400 text-xs" />
                            <span className="text-green-400 text-xs">
                              已保存结果
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <Tooltip title="删除记录">
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      loading={deleteLoading === item.id}
                      onClick={(e) => handleDeleteRecord(e, item.id)}
                      className="text-white/30 hover:text-red-400 hover:bg-red-500/10 border-none opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex-shrink-0"
                    />
                  </Tooltip>
                </div>
              </List.Item>
            )}
          />
        )}
      </div>

      <style jsx>{`
        .search-history-container {
          background: rgba(255, 255, 255, 0.02);
          border-radius: 12px;
          padding: 12px;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .search-history-list {
          overflow-y: auto;
        }

        .search-history-item {
          border: none !important;
          padding: 8px 0 !important;
        }

        .search-history-item:hover {
          background: rgba(255, 255, 255, 0.05) !important;
        }

        /* 自定义滚动条 */
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 2px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 2px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  )
}

export default SearchHistory
