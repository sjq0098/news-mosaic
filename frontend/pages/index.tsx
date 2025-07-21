import React, { useState, useEffect } from 'react'
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
  LoginOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useRouter } from 'next/router'
import NewsSearchSection from '../components/NewsSearchSection'
import ChatSection from '../components/ChatSection'
import NewsCardsSection from '../components/NewsCardsSection'
import AnalyticsSection from '../components/AnalyticsSection'
import UnifiedNewsProcessor from '../components/UnifiedNewsProcessor'
import { checkApiHealth } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const { Header, Sider, Content } = Layout

type TabKey = 'unified' | 'search' | 'chat' | 'cards' | 'analytics'

interface HomePageProps {
  toggleTheme?: () => void
  isDarkMode?: boolean
}

export default function HomePage({ toggleTheme, isDarkMode }: HomePageProps) {
  const router = useRouter()
  const { user, isAuthenticated, logout, isLoading } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<TabKey>('unified')
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

  // 侧边栏菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: 'unified',
      icon: <ThunderboltOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">统一处理</span>
          {!collapsed && <span className="text-xs bg-gradient-to-r from-blue-500 to-purple-500 text-white px-2 py-1 rounded-full">NEW</span>}
        </div>
      ),
    },
    {
      key: 'search',
      icon: <SearchOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">新闻搜索</span>
          {!collapsed && <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">SerpAPI</span>}
        </div>
      ),
    },
    {
      key: 'chat',
      icon: <MessageOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">AI对话</span>
          {!collapsed && <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded-full">通义千问</span>}
        </div>
      ),
    },
    {
      key: 'cards',
      icon: <FileTextOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">新闻卡片</span>
          {!collapsed && <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">智能生成</span>}
        </div>
      ),
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined className="text-lg" />,
      label: (
        <div className="flex items-center justify-between">
          <span className="font-medium">数据分析</span>
          {!collapsed && <span className="text-xs bg-orange-500/20 text-orange-300 px-2 py-1 rounded-full">趋势</span>}
        </div>
      ),
    },
  ]

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

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    setActiveTab(key as TabKey)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        message.info('个人资料功能开发中...')
        break
      case 'settings':
        router.push('/settings')
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

  // 渲染内容区域
  const renderContent = () => {
    // 如果是新用户，显示欢迎界面
    if (user && !user.preferences && activeTab === 'search') {
      return (
        <div className="max-w-4xl mx-auto">
          <Card className="text-center p-8 shadow-xl border-0 rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50">
            <div className="mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <ThunderboltOutlined className="text-white text-3xl" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                欢迎使用 News Mosaic！
              </h2>
              <p className="text-gray-600 text-lg">
                智能新闻分析平台，为您提供个性化的新闻搜索和分析服务
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              <div className="p-6 bg-white rounded-xl shadow-sm">
                <SearchOutlined className="text-blue-500 text-2xl mb-3" />
                <h3 className="font-semibold text-gray-800 mb-2">智能新闻搜索</h3>
                <p className="text-gray-600 text-sm">使用 SerpAPI 搜索最新新闻，支持多种筛选条件</p>
              </div>

              <div className="p-6 bg-white rounded-xl shadow-sm">
                <MessageOutlined className="text-green-500 text-2xl mb-3" />
                <h3 className="font-semibold text-gray-800 mb-2">AI 智能对话</h3>
                <p className="text-gray-600 text-sm">与通义千问模型对话，获得专业的新闻分析</p>
              </div>

              <div className="p-6 bg-white rounded-xl shadow-sm">
                <FileTextOutlined className="text-purple-500 text-2xl mb-3" />
                <h3 className="font-semibold text-gray-800 mb-2">新闻卡片生成</h3>
                <p className="text-gray-600 text-sm">自动生成结构化新闻卡片，包含摘要和分析</p>
              </div>

              <div className="p-6 bg-white rounded-xl shadow-sm">
                <BarChartOutlined className="text-orange-500 text-2xl mb-3" />
                <h3 className="font-semibold text-gray-800 mb-2">数据分析</h3>
                <p className="text-gray-600 text-sm">深度分析新闻趋势和情感倾向</p>
              </div>
            </div>

            <div className="mt-8">
              <Button
                type="primary"
                size="large"
                className="bg-gradient-to-r from-blue-500 to-purple-600 border-0 px-8"
                onClick={() => setActiveTab('unified')}
              >
                开始使用
              </Button>
            </div>
          </Card>
        </div>
      )
    }

    switch (activeTab) {
      case 'unified':
        return <UnifiedNewsProcessor />
      case 'search':
        return <NewsSearchSection />
      case 'chat':
        return <ChatSection />
      case 'cards':
        return <NewsCardsSection />
      case 'analytics':
        return <AnalyticsSection />
      default:
        return <UnifiedNewsProcessor />
    }
  }

  // 获取页面标题
  const getPageTitle = () => {
    const titles = {
      unified: '统一新闻处理',
      search: '智能新闻搜索',
      chat: 'AI智能对话',
      cards: '新闻卡片管理',
      analytics: '数据分析中心'
    }
    return titles[activeTab]
  }

  // 获取页面描述
  const getPageDescription = () => {
    const descriptions = {
      unified: '一站式新闻处理：搜索→存储→向量化→AI分析→卡片生成→智能对话',
      search: '使用 SerpAPI 搜索最新新闻，自动生成分析卡片和AI摘要',
      chat: '与通义千问模型对话，获得专业的新闻分析和见解',
      cards: '查看和管理生成的新闻卡片，包含情感分析和关键信息',
      analytics: '深度分析新闻趋势、情感倾向和热点话题'
    }
    return descriptions[activeTab]
  }

  // 如果正在加载认证状态，显示加载页面
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <Card className="text-center p-8 shadow-xl border-0 rounded-2xl">
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
    <Layout className="min-h-screen">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="modern-sidebar"
        width={260}
      >
        {/* Logo区域 */}
        <div className="h-20 flex items-center justify-center border-b border-white/10 relative overflow-hidden">
          {/* 背景装饰 */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-600/10"></div>

          <div className="flex items-center space-x-3 fade-in relative z-10">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform duration-300 cursor-pointer">
              <ThunderboltOutlined className="text-white text-xl" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-lg font-bold text-white bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  News Mosaic
                </span>
                <span className="text-xs text-white/60 font-medium">
                  智能新闻分析平台
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 菜单 */}
        <div className="px-3 mt-6">
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[activeTab]}
            items={menuItems}
            onClick={handleMenuClick}
            className="border-none bg-transparent"
          />
        </div>

        {/* API状态指示器和用户信息 */}
        {!collapsed && (
          <div className="absolute bottom-4 left-4 right-4 space-y-3">
            {/* 用户信息卡片 */}
            <div className="glass-card p-3 bg-white/5">
              <div className="flex items-center space-x-3">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-blue-500 to-purple-600"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">
                    {user?.nickname || user?.username || '用户'}
                  </p>
                  <p className="text-white/60 text-xs">
                    {user?.role === 'admin' ? '管理员' : '普通用户'}
                  </p>
                </div>
              </div>
            </div>

            {/* API状态指示器 */}
            <div className={`status-indicator ${
              apiStatus === 'online'
                ? 'status-online'
                : apiStatus === 'offline'
                ? 'status-offline'
                : 'status-loading'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'online' ? 'bg-green-400 animate-pulse' :
                apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400 animate-pulse'
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
        {/* 顶部导航 */}
        <Header className="modern-header px-4 md:px-6 flex items-center justify-between h-16 md:h-20">
          <div className="flex items-center space-x-4 md:space-x-6">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-white/80 hover:text-white hover:bg-white/10 border-none w-8 h-8 md:w-10 md:h-10 rounded-lg transition-all duration-300 hover:scale-110"
              size="large"
            />

            {/* 面包屑导航 */}
            <div className="hidden md:flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-white/60 text-sm">
                <span>News Mosaic</span>
                <span>/</span>
                <span className="text-white font-medium">{getPageTitle()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3 md:space-x-6">
            {/* 快捷操作按钮 - 仅在大屏幕显示 */}
            <div className="hidden lg:flex items-center space-x-2">
              <Button
                type="text"
                icon={<SearchOutlined />}
                onClick={() => setActiveTab('search')}
                className="text-white/70 hover:text-white hover:bg-white/10 border-none rounded-lg"
                disabled={activeTab === 'search'}
              >
                搜索
              </Button>
              <Button
                type="text"
                icon={<MessageOutlined />}
                onClick={() => setActiveTab('chat')}
                className="text-white/70 hover:text-white hover:bg-white/10 border-none rounded-lg"
                disabled={activeTab === 'chat'}
              >
                对话
              </Button>
            </div>

            {/* 主题切换 */}
            <div className="flex items-center space-x-2 md:space-x-3 bg-white/10 backdrop-blur-sm rounded-full px-3 py-2">
              <SunOutlined className="text-yellow-300 text-sm md:text-lg" />
              <Switch
                checked={isDarkMode}
                onChange={toggleTheme}
                size="small"
                className="bg-white/20"
              />
              <MoonOutlined className="text-blue-300 text-sm md:text-lg" />
            </div>

            {/* 用户菜单 */}
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div className="flex items-center space-x-2 md:space-x-3 cursor-pointer hover:bg-white/10 px-3 py-2 rounded-xl transition-all duration-300 backdrop-blur-sm border border-white/10">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-blue-500 to-purple-600 border-2 border-white/20"
                />
                <span className="hidden md:block text-white/90 text-sm font-medium">
                  {isAuthenticated ? (user?.nickname || user?.username || '用户') : '未登录'}
                </span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content className="p-4 md:p-8 overflow-auto custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            {/* 页面标题区域 */}
            <div className="mb-6 fade-in">
              <div className="glass-card p-6 mb-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="mb-4 md:mb-0">
                    <h1 className="text-2xl md:text-3xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                      {getPageTitle()}
                    </h1>
                    <p className="text-white/70 text-sm md:text-base">
                      {getPageDescription()}
                    </p>
                  </div>

                  {/* 快捷操作按钮 */}
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="primary"
                      icon={<SearchOutlined />}
                      className="modern-button"
                      onClick={() => setActiveTab('search')}
                      disabled={activeTab === 'search'}
                    >
                      搜索新闻
                    </Button>
                    <Button
                      type="default"
                      icon={<MessageOutlined />}
                      className="modern-button"
                      onClick={() => setActiveTab('chat')}
                      disabled={activeTab === 'chat'}
                    >
                      AI对话
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* 主要内容区域 */}
            <div className="fade-in">
              <div className="glass-card p-6 min-h-[600px]">
                {renderContent()}
              </div>
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}