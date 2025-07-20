import React, { useState, useRef, useEffect } from 'react'
import { 
  Card, 
  Input, 
  Button, 
  Space, 
  Avatar, 
  Spin, 
  message, 
  Divider,
  Tag,
  Tooltip
} from 'antd'
import { 
  SendOutlined, 
  RobotOutlined, 
  UserOutlined, 
  ClearOutlined,
  SoundOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined,
  MessageOutlined,
  BulbOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import dayjs from 'dayjs'
import { chatApi } from '../services/api'

const { TextArea } = Input

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  loading?: boolean
  news_cards?: any[]
  sources?: string[]
}

interface ChatSession {
  sessionId: string
  messages: ChatMessage[]
}

export default function ChatSection() {
  const [currentSession, setCurrentSession] = useState<ChatSession>({
    sessionId: 'default',
    messages: []
  })
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentSession.messages])

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入消息内容')
      return
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    }

    // 添加用户消息
    setCurrentSession(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage]
    }))

    const currentInput = inputValue.trim()
    setInputValue('')
    setIsLoading(true)
    setIsTyping(true)

    try {
      // 添加加载消息
      const loadingMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        loading: true
      }

      setCurrentSession(prev => ({
        ...prev,
        messages: [...prev.messages, loadingMessage]
      }))

      // 调用聊天API
      const response = await chatApi.sendMessage({
        content: currentInput,
        session_id: currentSession.sessionId,
        include_news: true,
        news_limit: 5
      })

      // 从响应中提取最新的AI消息
      const aiMessages = response.data.messages.filter((msg: any) => msg.role === 'assistant')
      const latestAiMessage = aiMessages[aiMessages.length - 1]

      // 移除加载消息并添加实际回复
      const assistantMessage: ChatMessage = {
        id: latestAiMessage?.id || (Date.now() + 2).toString(),
        type: 'assistant',
        content: latestAiMessage?.content || '抱歉，我现在无法回答这个问题。',
        timestamp: latestAiMessage?.created_at || new Date().toISOString(),
        news_cards: latestAiMessage?.news_ids ? [] : undefined, // 暂时为空，后续可扩展
        sources: [] // 暂时为空，后续可扩展
      }

      setCurrentSession(prev => ({
        ...prev,
        sessionId: response.data.session.id, // 更新会话ID
        messages: prev.messages.slice(0, -1).concat(assistantMessage)
      }))

    } catch (error) {
      console.error('Chat error:', error)
      
      // 移除加载消息并添加错误消息
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: '抱歉，服务暂时不可用，请稍后再试。',
        timestamp: new Date().toISOString()
      }

      setCurrentSession(prev => ({
        ...prev,
        messages: prev.messages.slice(0, -1).concat(errorMessage)
      }))
      
      message.error('发送失败，请稍后重试')
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  // 清空对话
  const handleClearChat = () => {
    setCurrentSession({
      sessionId: Date.now().toString(),
      messages: []
    })
    message.success('对话已清空')
  }

  // 复制消息
  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    message.success('已复制到剪贴板')
  }

  // 格式化时间
  const formatTime = (timestamp: string) => {
    return dayjs(timestamp).format('HH:mm')
  }

  // 渲染消息
  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user'
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
        <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-4 max-w-4xl w-full`}>
          {/* 头像 */}
          <Avatar
            size={40}
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            className={`flex-shrink-0 ${isUser ? 'ml-4' : 'mr-4'} shadow-lg`}
            style={{
              background: isUser 
                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' 
                : 'linear-gradient(135deg, #10b981, #34d399)'
            }}
          />
          
          {/* 消息内容 */}
          <div className={`flex-1 ${isUser ? 'mr-4' : 'ml-4'}`}>
            <div
              className={`
                message-bubble ${isUser ? 'user' : 'assistant'}
                ${message.loading ? 'loading-pulse' : ''}
              `}
            >
              {message.loading ? (
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-gray-500 font-medium">AI正在思考中...</span>
                </div>
              ) : (
                <div>
                  <ReactMarkdown
                    className={`prose prose-sm max-w-none ${
                      isUser ? 'prose-invert' : 'dark:prose-invert'
                    }`}
                  >
                    {message.content}
                  </ReactMarkdown>
                  
                  {/* 新闻卡片 */}
                  {message.news_cards && message.news_cards.length > 0 && (
                    <div className="mt-4 space-y-3">
                      <Divider className="my-3">
                        <span className="text-sm text-gray-500 font-medium flex items-center">
                          <BulbOutlined className="mr-2" />
                          相关新闻推荐
                        </span>
                      </Divider>
                      {message.news_cards.slice(0, 3).map((card, index) => (
                        <div key={index} className="glass-card p-4 hover:scale-105 transition-all duration-300">
                          <h4 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                            {card.title}
                          </h4>
                          <p className="text-gray-600 dark:text-gray-400 text-xs line-clamp-2 leading-relaxed">
                            {card.summary}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 来源信息 */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="text-xs text-gray-500 font-medium">来源：</span>
                      {message.sources.slice(0, 3).map((source, index) => (
                        <Tag key={index} className="text-xs rounded-full border-0 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                          {source}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {/* 消息操作和时间 */}
            <div className={`flex items-center justify-between mt-2 px-2 ${isUser ? 'flex-row-reverse' : ''}`}>
              <span className="text-xs text-gray-500 font-medium">
                {formatTime(message.timestamp)}
              </span>
              
              {!message.loading && (
                <div className={`flex items-center space-x-1 ${isUser ? 'mr-2' : 'ml-2'}`}>
                  <Tooltip title="复制">
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleCopyMessage(message.content)}
                      className="text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-full w-7 h-7 flex items-center justify-center transition-all duration-300"
                    />
                  </Tooltip>
                  
                  {!isUser && (
                    <>
                      <Tooltip title="有帮助">
                        <Button
                          type="text"
                          size="small"
                          icon={<LikeOutlined />}
                          className="text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900 rounded-full w-7 h-7 flex items-center justify-center transition-all duration-300"
                        />
                      </Tooltip>
                      <Tooltip title="无帮助">
                        <Button
                          type="text"
                          size="small"
                          icon={<DislikeOutlined />}
                          className="text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-full w-7 h-7 flex items-center justify-center transition-all duration-300"
                        />
                      </Tooltip>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 欢迎横幅 */}
      <div className="glass-card p-8 text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mr-4">
            <MessageOutlined className="text-white text-2xl" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
            AI智能对话
          </h2>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          与AI新闻助手对话，获取实时新闻分析和个性化推荐
        </p>
      </div>

      {/* 聊天容器 */}
      <div className="glass-card overflow-hidden">
        {/* 聊天头部 */}
        <div className="px-6 py-4 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Avatar 
                size={48}
                icon={<RobotOutlined />} 
                className="shadow-lg float-animation" 
                style={{ background: 'linear-gradient(135deg, #10b981, #34d399)' }}
              />
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white m-0 flex items-center">
                  AI新闻助手
                  <ThunderboltOutlined className="ml-2 text-yellow-500" />
                </h3>
                <p className="text-sm text-gray-500 m-0 flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                  {isTyping ? '正在输入中...' : '在线 - 随时为您服务'}
                </p>
              </div>
            </div>
            
            <Space>
              <Tooltip title="清空对话">
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClearChat}
                  disabled={currentSession.messages.length === 0}
                  className="glass-card border-0 hover:scale-105 transition-all duration-300"
                >
                  清空对话
                </Button>
              </Tooltip>
            </Space>
          </div>
        </div>

        {/* 聊天内容区域 */}
        <div className="h-96 md:h-[500px] flex flex-col">
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6" style={{ minHeight: '400px' }}>
            {currentSession.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-24 h-24 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-800 dark:to-emerald-800 rounded-full flex items-center justify-center mb-6">
                  <RobotOutlined className="text-4xl text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-3">开始智能对话</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6 leading-relaxed">
                  您好！我是AI新闻助手，具备强大的新闻搜索、分析和推荐能力。
                  我可以帮您了解最新资讯、生成新闻卡片、分析舆情趋势。
                </p>
                <div className="flex flex-wrap gap-3 justify-center">
                  <Tag 
                    className="cursor-pointer px-4 py-2 rounded-full border-0 bg-gradient-to-r from-blue-100 to-blue-200 dark:from-blue-800 dark:to-blue-900 text-blue-700 dark:text-blue-300 hover:scale-105 transition-all duration-300 font-medium" 
                    onClick={() => setInputValue('最新科技新闻有哪些？')}
                  >
                    🔬 最新科技新闻
                  </Tag>
                  <Tag 
                    className="cursor-pointer px-4 py-2 rounded-full border-0 bg-gradient-to-r from-green-100 to-green-200 dark:from-green-800 dark:to-green-900 text-green-700 dark:text-green-300 hover:scale-105 transition-all duration-300 font-medium"
                    onClick={() => setInputValue('今日财经要闻总结')}
                  >
                    💰 今日财经要闻
                  </Tag>
                  <Tag 
                    className="cursor-pointer px-4 py-2 rounded-full border-0 bg-gradient-to-r from-purple-100 to-purple-200 dark:from-purple-800 dark:to-purple-900 text-purple-700 dark:text-purple-300 hover:scale-105 transition-all duration-300 font-medium"
                    onClick={() => setInputValue('体育赛事最新动态')}
                  >
                    ⚽ 体育赛事动态
                  </Tag>
                </div>
              </div>
            ) : (
              <>
                {currentSession.messages.map(renderMessage)}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* 输入区域 */}
          <div className="border-t border-white/10 p-4">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <TextArea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="输入您的问题，我会为您提供专业的新闻分析..."
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  className="modern-input resize-none"
                  disabled={isLoading}
                  maxLength={2000}
                />
              </div>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={isLoading}
                disabled={!inputValue.trim()}
                size="large"
                className="modern-button h-auto px-6 hover:scale-105 transition-all duration-300"
              >
                发送
              </Button>
            </div>
            <div className="mt-3 flex justify-between items-center text-xs text-gray-500">
              <span className="flex items-center">
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs mr-2">Enter</kbd>
                发送消息
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs ml-4 mr-2">Shift + Enter</kbd>
                换行
              </span>
              <span className={`font-medium ${inputValue.length > 1800 ? 'text-red-500' : 'text-gray-400'}`}>
                {inputValue.length}/2000
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}