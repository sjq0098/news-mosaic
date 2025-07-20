import React, { useState, useEffect } from 'react'
import { Layout, Menu, Button, Switch, Avatar, Dropdown, Space, message } from 'antd'
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
  ThunderboltOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import NewsSearchSection from '../components/NewsSearchSection'
import ChatSection from '../components/ChatSection'
import NewsCardsSection from '../components/NewsCardsSection'
import AnalyticsSection from '../components/AnalyticsSection'
import { checkApiHealth } from '../services/api'

const { Header, Sider, Content } = Layout

type TabKey = 'search' | 'chat' | 'cards' | 'analytics'

interface HomePageProps {
  toggleTheme?: () => void
  isDarkMode?: boolean
}

export default function HomePage({ toggleTheme, isDarkMode }: HomePageProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<TabKey>('search')
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking')

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
      key: 'search',
      icon: <SearchOutlined className="text-lg" />,
      label: <span className="font-medium">新闻搜索</span>,
    },
    {
      key: 'chat',
      icon: <MessageOutlined className="text-lg" />,
      label: <span className="font-medium">AI对话</span>,
    },
    {
      key: 'cards',
      icon: <FileTextOutlined className="text-lg" />,
      label: <span className="font-medium">新闻卡片</span>,
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined className="text-lg" />,
      label: <span className="font-medium">数据分析</span>,
    },
  ]

  // 用户菜单
  const userMenuItems: MenuProps['items'] = [
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
        message.info('设置功能开发中...')
        break
      case 'logout':
        message.success('已退出登录')
        break
    }
  }

  // 渲染内容区域
  const renderContent = () => {
    switch (activeTab) {
      case 'search':
        return <NewsSearchSection />
      case 'chat':
        return <ChatSection />
      case 'cards':
        return <NewsCardsSection />
      case 'analytics':
        return <AnalyticsSection />
      default:
        return <NewsSearchSection />
    }
  }

  // 获取页面标题
  const getPageTitle = () => {
    const titles = {
      search: '新闻搜索',
      chat: 'AI对话',
      cards: '新闻卡片',
      analytics: '数据分析'
    }
    return titles[activeTab]
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
        <div className="h-20 flex items-center justify-center border-b border-white/10">
          <div className="flex items-center space-x-3 fade-in">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <ThunderboltOutlined className="text-white text-xl" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-lg font-bold text-white bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  News Mosaic
                </span>
                <span className="text-xs text-white/60 font-medium">
                  智能新闻分析
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

        {/* API状态指示器 */}
        {!collapsed && (
          <div className="absolute bottom-6 left-4 right-4">
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
        <Header className="modern-header px-6 flex items-center justify-between h-20">
          <div className="flex items-center space-x-6">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-white/80 hover:text-white hover:bg-white/10 border-none w-10 h-10 rounded-lg transition-all duration-300 hover:scale-110"
              size="large"
            />
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-white m-0 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                {getPageTitle()}
              </h1>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            {/* 主题切换 */}
            <div className="flex items-center space-x-3 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
              <SunOutlined className="text-yellow-300 text-lg" />
              <Switch
                checked={isDarkMode}
                onChange={toggleTheme}
                size="default"
                className="bg-white/20"
              />
              <MoonOutlined className="text-blue-300 text-lg" />
            </div>

            {/* 用户菜单 */}
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div className="flex items-center space-x-3 cursor-pointer hover:bg-white/10 px-4 py-2 rounded-xl transition-all duration-300 backdrop-blur-sm border border-white/10">
                <Avatar 
                  size="default" 
                  icon={<UserOutlined />} 
                  className="bg-gradient-to-br from-blue-500 to-purple-600 border-2 border-white/20" 
                />
                <span className="text-white/90 text-sm font-medium">
                  管理员
                </span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content className="p-8 overflow-auto custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            <div className="fade-in">
              {renderContent()}
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}