import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { searchHistoryApi } from '../services/api'

export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: string
  metadata?: any
  // 保存完整的搜索结果
  searchResult?: any
  chatMessages?: any[]
  sessionId?: string
}

const STORAGE_KEY = 'news_mosaic_search_history'
const MAX_HISTORY_ITEMS = 50

export const useSearchHistory = () => {
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])
  const [loading, setLoading] = useState(false)

  // 从本地存储加载搜索历史
  const loadLocalHistory = useCallback(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const history = JSON.parse(stored)
        setSearchHistory(Array.isArray(history) ? history : [])
      }
    } catch (error) {
      console.error('加载本地搜索历史失败:', error)
      setSearchHistory([])
    }
  }, [])

  // 保存到本地存储
  const saveToLocal = useCallback((history: SearchHistoryItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history))
    } catch (error) {
      console.error('保存搜索历史到本地失败:', error)
    }
  }, [])

  // 添加搜索记录
  const addSearchRecord = useCallback(async (
    query: string,
    metadata?: any,
    searchResult?: any,
    chatMessages?: any[],
    sessionId?: string
  ) => {
    if (!query.trim()) return

    const newRecord: SearchHistoryItem = {
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      query: query.trim(),
      timestamp: new Date().toISOString(),
      metadata,
      searchResult,
      chatMessages,
      sessionId
    }

    setSearchHistory(prev => {
      // 检查是否已存在相同的查询
      const existingIndex = prev.findIndex(item => item.query === newRecord.query)
      let newHistory: SearchHistoryItem[]

      if (existingIndex >= 0) {
        // 如果存在，更新时间戳、搜索结果和对话记录，并移到最前面
        newHistory = [
          {
            ...prev[existingIndex],
            timestamp: newRecord.timestamp,
            searchResult: newRecord.searchResult,
            chatMessages: newRecord.chatMessages,
            sessionId: newRecord.sessionId,
            metadata: newRecord.metadata
          },
          ...prev.slice(0, existingIndex),
          ...prev.slice(existingIndex + 1)
        ]
      } else {
        // 如果不存在，添加到最前面
        newHistory = [newRecord, ...prev]
      }

      // 限制历史记录数量
      if (newHistory.length > MAX_HISTORY_ITEMS) {
        newHistory = newHistory.slice(0, MAX_HISTORY_ITEMS)
      }

      // 保存到本地存储
      saveToLocal(newHistory)
      return newHistory
    })

    // 尝试同步到服务器（如果用户已登录）
    try {
      await searchHistoryApi.addSearchRecord({
        query: newRecord.query,
        timestamp: newRecord.timestamp,
        metadata
      })
    } catch (error) {
      // 服务器同步失败不影响本地功能
      console.warn('同步搜索历史到服务器失败:', error)
    }
  }, [saveToLocal])

  // 删除搜索记录
  const deleteSearchRecord = useCallback(async (recordId: string) => {
    setSearchHistory(prev => {
      const newHistory = prev.filter(item => item.id !== recordId)
      saveToLocal(newHistory)
      return newHistory
    })

    // 尝试从服务器删除
    try {
      await searchHistoryApi.deleteSearchRecord(recordId)
    } catch (error) {
      console.warn('从服务器删除搜索记录失败:', error)
    }
  }, [saveToLocal])

  // 清空搜索历史
  const clearSearchHistory = useCallback(async () => {
    setSearchHistory([])
    saveToLocal([])

    // 尝试清空服务器历史
    try {
      await searchHistoryApi.clearSearchHistory()
      message.success('搜索历史已清空')
    } catch (error) {
      console.warn('清空服务器搜索历史失败:', error)
      message.success('本地搜索历史已清空')
    }
  }, [saveToLocal])

  // 从服务器同步搜索历史
  const syncFromServer = useCallback(async () => {
    setLoading(true)
    try {
      const response = await searchHistoryApi.getSearchHistory(MAX_HISTORY_ITEMS)
      if (response.data.status === 'success' && Array.isArray(response.data.data)) {
        const serverHistory = response.data.data.map((item: any) => ({
          id: item._id || item.id || `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          query: item.query,
          timestamp: item.timestamp,
          metadata: item.metadata
        }))

        // 合并本地和服务器历史，去重并按时间排序
        setSearchHistory(prev => {
          const combined = [...serverHistory, ...prev]
          const uniqueMap = new Map<string, SearchHistoryItem>()
          
          combined.forEach(item => {
            const existing = uniqueMap.get(item.query)
            if (!existing || new Date(item.timestamp) > new Date(existing.timestamp)) {
              uniqueMap.set(item.query, item)
            }
          })

          const merged = Array.from(uniqueMap.values())
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
            .slice(0, MAX_HISTORY_ITEMS)

          saveToLocal(merged)
          return merged
        })
      }
    } catch (error) {
      console.warn('从服务器同步搜索历史失败:', error)
    } finally {
      setLoading(false)
    }
  }, [saveToLocal])

  // 获取搜索建议（基于历史记录）
  const getSearchSuggestions = useCallback((input: string, limit = 5) => {
    if (!input.trim()) return []
    
    const query = input.toLowerCase()
    return searchHistory
      .filter(item => item.query.toLowerCase().includes(query))
      .slice(0, limit)
      .map(item => item.query)
  }, [searchHistory])

  // 初始化
  useEffect(() => {
    loadLocalHistory()
  }, [loadLocalHistory])

  return {
    searchHistory,
    loading,
    addSearchRecord,
    deleteSearchRecord,
    clearSearchHistory,
    syncFromServer,
    getSearchSuggestions
  }
}
