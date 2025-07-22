import React, { useState, useEffect, useRef } from 'react'
import { Layout, Menu, Button, Switch, Avatar, Dropdown, Space, message, Card, Spin } from 'antd'
import {
  SearchOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
  ThunderboltOutlined,
  LoginOutlined,
  PlusOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useRouter } from 'next/router'
import UnifiedNewsProcessor, { UnifiedNewsProcessorRef } from '../components/UnifiedNewsProcessor'
import SearchHistory from '../components/SearchHistory'
import { checkApiHealth } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { SearchHistoryProvider } from '../contexts/SearchHistoryContext'

const { Header, Sider, Content } = Layout

// 移除多标签页类型定义，现在只有统一处理界面

interface HomePageProps {
  toggleTheme?: () => void
  isDarkMode?: boolean
}

export default function HomePage({ toggleTheme, isDarkMode }: HomePageProps) {
  const router = useRouter()
  const { user, isAuthenticated, logout, isLoading } = useAuth()
  const newsProcessorRef = useRef<UnifiedNewsProcessorRef>(null)
  const [collapsed, setCollapsed] = useState(false)
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking')

  // 强制登录检查
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      message.info('请先登录以使用完整功能')
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  // 检查API状态
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await checkApiHealth()
        setApiStatus('online')
      } catch (error) {
        setApiStatus('offline')
        message.warning('后端服务连接失败，部分功能将使用模拟数据')
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 30000) // 每30秒检查一次
    return () => clearInterval(interval)
  }, [])

  // 处理新搜索按钮点击
  const handleNewSearch = async () => {
    if (newsProcessorRef.current) {
      await newsProcessorRef.current.clearCurrentSession()
    }
  }

  // 简化的侧边栏菜单项（仅保留核心功能）
  const menuItems: MenuProps['items'] = [
    {
      key: 'unified',
      icon: <ThunderboltOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">统一新闻处理</span>
          {!collapsed && <span className="text-xs bg-gradient-to-r from-blue-500 to-purple-500 text-white px-2 py-1 rounded-full">主功能</span>}
        </div>
      ),
    },
  ]

  // 新搜索按钮（独立于菜单）
  const newSearchButton = (
    <div className="px-3 mt-4">
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={handleNewSearch}
        className="w-full bg-gradient-to-r from-green-500 to-blue-500 border-none hover:from-green-600 hover:to-blue-600 transition-all duration-300"
        size="large"
      >
        {!collapsed && '开启新搜索'}
      </Button>
    </div>
  )

  // 用户菜单
  const userMenuItems: MenuProps['items'] = isAuthenticated ? [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ] : [
    {
      key: 'login',
      icon: <LoginOutlined />,
      label: '登录',
    },
  ]

  // 处理菜单点击（现在只有统一处理功能）
  const handleMenuClick = ({ key }: { key: string }) => {
    // 现在只有一个主功能，不需要切换
    console.log('Menu clicked:', key)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        message.info('个人资料功能开发中...')
        break
      case 'settings':
        message.info('设置功能开发中...')
        break
      case 'logout':
        logout()
        break
      case 'login':
        router.push('/login')
        break
      default:
        break
    }
  }

  // 处理搜索历史选择
  const handleSearchHistorySelect = (query: string) => {
    if (newsProcessorRef.current) {
      newsProcessorRef.current.triggerSearch(query)
      message.success(`正在搜索: ${query}`)
    }
  }

  // 处理历史状态恢复
  const handleHistoryRestore = (historyItem: any) => {
    if (newsProcessorRef.current) {
      newsProcessorRef.current.restoreHistoryState(historyItem)
    }
  }

  // 渲染内容区域（现在只有统一新闻处理功能）
  const renderContent = () => {
    return <UnifiedNewsProcessor ref={newsProcessorRef} />
  }

  // 获取页面标题
  const getPageTitle = () => {
    return '智能新闻分析'
  }

  // 获取页面描述
  const getPageDescription = () => {
    return '发现新闻洞察，探索深度分析'
  }

  // 如果正在加载认证状态，显示加载页面 - 马卡农配色
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ 
        background: 'linear-gradient(135deg, rgba(253, 242, 248, 0.5) 0%, rgba(255, 251, 235, 0.5) 25%, rgba(240, 253, 244, 0.5) 50%, rgba(250, 245, 255, 0.5) 75%, rgba(255, 251, 235, 0.5) 100%)' 
      }}>
        <Card 
          className="text-center p-8 shadow-xl border-0 rounded-2xl"
          style={{
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.5)'
          }}
        >
          <Spin size="large" />
          <div className="mt-4">
            <h3 className="text-lg font-semibold text-gray-700">正在加载...</h3>
            <p className="text-gray-500 mt-2">请稍候，正在验证您的登录状态</p>
          </div>
        </Card>
      </div>
    )
  }

  // 如果未登录，不渲染主界面（会被重定向到登录页）
  if (!isAuthenticated) {
    return null
  }

  return (
    <SearchHistoryProvider>
      <Layout className="min-h-screen bg-gradient-to-br from-macaron-pink-light via-macaron-cream to-macaron-mint-light">
      {/* 侧边栏 - 马卡农配色 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="macaron-sidebar"
        width={260}
        style={{
          background: 'linear-gradient(180deg, rgba(250, 218, 221, 0.9) 0%, rgba(215, 240, 233, 0.9) 50%, rgba(232, 213, 255, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.3)'
        }}
      >
        {/* Logo区域 - 马卡农风格 */}
        <div className="h-20 flex items-center justify-center border-b border-macaron-pink/20 relative overflow-hidden">
          {/* 背景装饰 */}
          <div className="absolute inset-0 bg-gradient-to-r from-macaron-yellow/10 to-macaron-lavender/10"></div>

          <div className="flex items-center space-x-3 fade-in relative z-10">
            <div className="w-12 h-12 bg-gradient-to-br from-macaron-mint to-macaron-yellow rounded-xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform duration-300 cursor-pointer">
              <ThunderboltOutlined className="text-gray-700 text-xl" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-lg font-bold text-gray-800 bg-gradient-to-r from-macaron-pink to-macaron-lavender bg-clip-text text-transparent">
                  News Mosaic
                </span>
                <span className="text-xs text-gray-600 font-medium">
                  智能新闻分析平台
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 菜单 - 马卡农主题 */}
        <div className="px-3 mt-6">
          <Menu
            mode="inline"
            selectedKeys={['unified']}
            items={menuItems}
            onClick={handleMenuClick}
            className="border-none bg-transparent macaron-menu"
            style={{
              background: 'transparent',
              color: '#4A5568'
            }}
          />
        </div>

        {/* 新搜索按钮 - 马卡农风格 */}
        <div className="px-3 mt-4">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleNewSearch}
            className="w-full bg-gradient-to-r from-macaron-mint to-macaron-yellow border-none hover:from-macaron-pink hover:to-macaron-lavender transition-all duration-300 text-gray-700 font-medium shadow-md hover:shadow-lg"
            size="large"
            style={{
              borderRadius: '12px',
              height: '44px'
            }}
          >
            {!collapsed && '开启新搜索'}
          </Button>
        </div>

        {/* 搜索历史区域 */}
        {!collapsed && (
          <div className="px-3 mt-6 flex-1 overflow-hidden">
            <SearchHistory
              onSearchSelect={handleSearchHistorySelect}
              onHistoryRestore={handleHistoryRestore}
              maxHeight="calc(100vh - 400px)"
            />
          </div>
        )}

        {/* 底部固定区域：用户信息和API状态 - 马卡农风格 */}
        {!collapsed && (
          <div className="absolute bottom-0 left-0 right-0 p-4 space-y-3 bg-gradient-to-t from-macaron-cream/80 to-transparent backdrop-blur-sm">
            {/* 用户信息卡片 */}
            <div className="bg-white/60 backdrop-filter backdrop-blur-sm p-3 rounded-2xl border border-white/30 shadow-sm">
              <div className="flex items-center space-x-3">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-macaron-pink to-macaron-lavender"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-800 text-sm font-medium truncate">
                    {user?.nickname || user?.username || '用户'}
                  </p>
                  <p className="text-gray-600 text-xs">
                    {user?.role === 'admin' ? '管理员' : '普通用户'}
                  </p>
                </div>
              </div>
            </div>

            {/* API状态指示器 */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl backdrop-filter backdrop-blur-sm border ${
              apiStatus === 'online'
                ? 'bg-macaron-mint/40 text-green-700 border-green-200'
                : apiStatus === 'offline'
                ? 'bg-macaron-pink/40 text-red-700 border-red-200'
                : 'bg-macaron-yellow/40 text-yellow-700 border-yellow-200'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'online' ? 'bg-green-500 animate-pulse' :
                apiStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
              }`} />
              <span className="text-sm font-medium">
                {apiStatus === 'online' ? '服务正常' :
                 apiStatus === 'offline' ? '服务离线' : '检查中...'}
              </span>
            </div>
          </div>
        )}
      </Sider>

      {/* 主内容区域 */}
      <Layout>
        {/* 顶部导航 - 马卡农渐变背景 */}
        <Header 
          className="px-4 md:px-6 flex items-center justify-between h-16 md:h-20 border-b border-white/20"
          style={{
            background: 'linear-gradient(90deg, rgba(250, 218, 221, 0.8) 0%, rgba(255, 242, 204, 0.8) 50%, rgba(215, 240, 233, 0.8) 100%)',
            backdropFilter: 'blur(20px)'
          }}
        >
          <div className="flex items-center space-x-4 md:space-x-6">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-gray-700 hover:text-gray-900 hover:bg-white/20 border-none w-8 h-8 md:w-10 md:h-10 rounded-lg transition-all duration-300 hover:scale-110"
              size="large"
            />

            {/* 面包屑导航 */}
            <div className="hidden md:flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-gray-600 text-sm">
                <span>News Mosaic</span>
                <span>/</span>
                <span className="text-gray-800 font-medium">{getPageTitle()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3 md:space-x-6">
            {/* 功能说明 - 仅在大屏幕显示 */}
            <div className="hidden lg:flex items-center space-x-2">
              <span className="text-gray-600 text-sm">
                一站式新闻处理平台
              </span>
            </div>

            {/* 主题切换 - 马卡农风格 */}
            <div className="flex items-center space-x-2 md:space-x-3 bg-white/30 backdrop-blur-sm rounded-full px-3 py-2 border border-white/20">
              <SunOutlined className="text-macaron-yellow text-sm md:text-lg" />
              <Switch
                checked={isDarkMode}
                onChange={toggleTheme}
                size="small"
                className="bg-macaron-lavender/30"
              />
              <MoonOutlined className="text-macaron-lavender text-sm md:text-lg" />
            </div>

            {/* 用户菜单 */}
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div className="flex items-center space-x-2 md:space-x-3 cursor-pointer hover:bg-white/20 px-3 py-2 rounded-xl transition-all duration-300 backdrop-blur-sm border border-white/20">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-macaron-mint to-macaron-pink border-2 border-white/20"
                />
                <span className="hidden md:block text-gray-800 text-sm font-medium">
                  {isAuthenticated ? (user?.nickname || user?.username || '用户') : '未登录'}
                </span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 - 马卡农背景 */}
        <Content 
          className="p-4 md:p-8 overflow-auto custom-scrollbar"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 251, 235, 0.3) 0%, rgba(253, 242, 248, 0.3) 25%, rgba(240, 253, 244, 0.3) 50%, rgba(250, 245, 255, 0.3) 75%, rgba(255, 251, 235, 0.3) 100%)'
          }}
        >
          <div className="max-w-7xl mx-auto">
            {/* 页面标题区域 - 马卡农卡片风格 */}
            <div className="mb-6 fade-in">
              <div 
                className="p-6 mb-6 rounded-3xl border shadow-lg"
                style={{
                  background: 'rgba(255, 255, 255, 0.7)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.5)'
                }}
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="mb-4 md:mb-0">
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2 bg-gradient-to-r from-macaron-pink to-macaron-lavender bg-clip-text text-transparent">
                      {getPageTitle()}
                    </h1>
                    <p className="text-gray-600 text-sm md:text-base">
                      {getPageDescription()}
                    </p>
                  </div>

                  {/* API状态指示器 */}
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      apiStatus === 'online' ? 'bg-green-400' :
                      apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
                    }`}></div>
                    <span className="text-gray-600 text-sm">
                      {apiStatus === 'online' ? '服务正常' :
                       apiStatus === 'offline' ? '服务离线' : '检查中...'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 主要内容区域 - 马卡农卡片 */}
            <div className="fade-in">
              <div 
                className="p-6 min-h-[600px] rounded-3xl border shadow-lg"
                style={{
                  background: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.6)'
                }}
              >
                {renderContent()}
              </div>
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
    </SearchHistoryProvider>
  )
}