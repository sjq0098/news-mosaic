import React, { useState } from 'react'
import { Layout, Menu, Card, Tabs, Button, Space, message } from 'antd'
import { 
  UserOutlined, 
  SettingOutlined, 
  HeartOutlined, 
  HistoryOutlined,
  ArrowLeftOutlined,
  SafetyOutlined
} from '@ant-design/icons'
import { useRouter } from 'next/router'
import ProtectedRoute from '../components/ProtectedRoute'
import UserPreferences from '../components/UserPreferences'
import PersonalizedNews from '../components/PersonalizedNews'
import { useAuth } from '../contexts/AuthContext'

const { Content, Sider } = Layout
const { TabPane } = Tabs

export default function SettingsPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')

  // 侧边栏菜单项
  const menuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'preferences',
      icon: <SettingOutlined />,
      label: '偏好设置',
    },
    {
      key: 'personalized',
      icon: <HeartOutlined />,
      label: '个性化推荐',
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: '阅读历史',
    },
    {
      key: 'security',
      icon: <SafetyOutlined />,
      label: '安全设置',
    },
  ]

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    setActiveTab(key)
  }

  // 渲染内容
  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <Card title="个人资料" className="h-full">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <div className="text-lg">{user?.username}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <div className="text-lg">{user?.email || '未设置'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">昵称</label>
                <div className="text-lg">{user?.nickname || '未设置'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                <div className="text-lg">{user?.role === 'admin' ? '管理员' : '普通用户'}</div>
              </div>
              <Button type="primary">编辑资料</Button>
            </div>
          </Card>
        )
      
      case 'preferences':
        return <UserPreferences />
      
      case 'personalized':
        return (
          <div>
            <Card title="个性化推荐" className="mb-4">
              <p className="text-gray-600 mb-4">
                基于您的阅读偏好和行为，为您推荐感兴趣的新闻内容。
              </p>
            </Card>
            <PersonalizedNews limit={20} showHeader={true} />
          </div>
        )
      
      case 'history':
        return (
          <Card title="阅读历史" className="h-full">
            <div className="text-center py-8">
              <HistoryOutlined className="text-4xl text-gray-400 mb-4" />
              <p className="text-gray-500">阅读历史功能开发中...</p>
            </div>
          </Card>
        )
      
      case 'security':
        return (
          <Card title="安全设置" className="h-full">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">密码设置</h3>
                <p className="text-gray-600 mb-4">定期更改密码以保护账户安全</p>
                <Button type="primary">修改密码</Button>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-2">登录设备</h3>
                <p className="text-gray-600 mb-4">管理您的登录设备和会话</p>
                <Button>查看登录设备</Button>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-2">账户注销</h3>
                <p className="text-gray-600 mb-4">永久删除您的账户和所有数据</p>
                <Button danger>注销账户</Button>
              </div>
            </div>
          </Card>
        )
      
      default:
        return null
    }
  }

  return (
    <ProtectedRoute>
      <Layout className="min-h-screen bg-gray-50">
        {/* 顶部导航 */}
        <div className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-4">
              <Button 
                type="text" 
                icon={<ArrowLeftOutlined />}
                onClick={() => router.push('/')}
                className="hover:bg-gray-100"
              >
                返回首页
              </Button>
              <h1 className="text-2xl font-bold text-gray-800">设置中心</h1>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-gray-600">欢迎，</span>
              <span className="font-medium">{user?.nickname || user?.username}</span>
            </div>
          </div>
        </div>

        <Layout className="max-w-7xl mx-auto w-full">
          {/* 侧边栏 */}
          <Sider 
            width={250} 
            className="bg-white shadow-sm"
            style={{ height: 'calc(100vh - 73px)' }}
          >
            <div className="p-4">
              <Menu
                mode="inline"
                selectedKeys={[activeTab]}
                items={menuItems}
                onClick={handleMenuClick}
                className="border-none"
              />
            </div>
          </Sider>

          {/* 主内容区 */}
          <Content className="p-6 bg-gray-50">
            <div className="h-full">
              {renderContent()}
            </div>
          </Content>
        </Layout>
      </Layout>
    </ProtectedRoute>
  )
}
