import React from 'react'
import { Card, Button, Space, Typography, Divider, Alert } from 'antd'
import { UserOutlined, LoginOutlined, SettingOutlined, HeartOutlined } from '@ant-design/icons'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'

const { Title, Paragraph, Text } = Typography

export default function DemoPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()

  const features = [
    {
      title: '用户注册与登录',
      description: '支持用户名/邮箱登录，JWT token认证，密码加密存储',
      icon: <UserOutlined className="text-blue-500" />,
      implemented: true
    },
    {
      title: '个人偏好设置',
      description: '用户可以设置新闻分类偏好、关键词兴趣、语言时区等',
      icon: <SettingOutlined className="text-green-500" />,
      implemented: true
    },
    {
      title: '个性化推荐',
      description: '基于用户偏好和行为历史，提供个性化新闻推荐',
      icon: <HeartOutlined className="text-red-500" />,
      implemented: true
    },
    {
      title: '用户行为追踪',
      description: '记录用户阅读、点赞、分享等行为，用于改进推荐算法',
      icon: <LoginOutlined className="text-purple-500" />,
      implemented: true
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* 页面标题 */}
        <div className="text-center mb-8">
          <Title level={1} className="mb-4">
            News Mosaic 登录功能演示
          </Title>
          <Paragraph className="text-lg text-gray-600">
            完整的用户认证系统，支持个性化体验
          </Paragraph>
        </div>

        {/* 当前登录状态 */}
        <Card className="mb-8 shadow-lg">
          <Title level={3}>当前登录状态</Title>
          {isAuthenticated ? (
            <Alert
              message="已登录"
              description={
                <div>
                  <p><strong>用户名:</strong> {user?.username}</p>
                  <p><strong>邮箱:</strong> {user?.email || '未设置'}</p>
                  <p><strong>昵称:</strong> {user?.nickname || '未设置'}</p>
                  <p><strong>角色:</strong> {user?.role === 'admin' ? '管理员' : '普通用户'}</p>
                </div>
              }
              type="success"
              showIcon
              action={
                <Space direction="vertical">
                  <Button size="small" onClick={() => router.push('/settings')}>
                    个人设置
                  </Button>
                  <Button size="small" onClick={() => router.push('/')}>
                    返回首页
                  </Button>
                </Space>
              }
            />
          ) : (
            <Alert
              message="未登录"
              description="请先登录以体验个性化功能"
              type="warning"
              showIcon
              action={
                <Space>
                  <Button size="small" type="primary" onClick={() => router.push('/login')}>
                    立即登录
                  </Button>
                  <Button size="small" onClick={() => router.push('/')}>
                    返回首页
                  </Button>
                </Space>
              }
            />
          )}
        </Card>

        {/* 功能特性 */}
        <Card className="mb-8 shadow-lg">
          <Title level={3}>已实现的功能特性</Title>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <Card key={index} type="inner" className="h-full">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{feature.icon}</div>
                  <div className="flex-1">
                    <Title level={5} className="mb-2">{feature.title}</Title>
                    <Paragraph className="text-gray-600 mb-3">
                      {feature.description}
                    </Paragraph>
                    <Text 
                      type={feature.implemented ? "success" : "secondary"}
                      className="font-medium"
                    >
                      {feature.implemented ? "✅ 已实现" : "🚧 开发中"}
                    </Text>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        {/* 技术架构 */}
        <Card className="mb-8 shadow-lg">
          <Title level={3}>技术架构</Title>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Title level={5}>后端技术栈</Title>
              <ul className="space-y-2 text-gray-600">
                <li>• FastAPI - 现代化的Python Web框架</li>
                <li>• MongoDB - 文档数据库存储用户数据</li>
                <li>• JWT - JSON Web Token认证</li>
                <li>• bcrypt - 密码加密</li>
                <li>• Pydantic - 数据验证和序列化</li>
              </ul>
            </div>
            <div>
              <Title level={5}>前端技术栈</Title>
              <ul className="space-y-2 text-gray-600">
                <li>• Next.js - React全栈框架</li>
                <li>• TypeScript - 类型安全的JavaScript</li>
                <li>• Ant Design - 企业级UI组件库</li>
                <li>• Context API - 状态管理</li>
                <li>• Axios - HTTP客户端</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 使用说明 */}
        <Card className="shadow-lg">
          <Title level={3}>使用说明</Title>
          <div className="space-y-4">
            <div>
              <Title level={5}>1. 用户注册</Title>
              <Paragraph>
                点击"立即登录"按钮，切换到注册标签页，填写用户名、邮箱、密码等信息完成注册。
              </Paragraph>
            </div>
            
            <div>
              <Title level={5}>2. 用户登录</Title>
              <Paragraph>
                使用注册的用户名或邮箱和密码登录系统，登录成功后会自动跳转到首页。
              </Paragraph>
            </div>
            
            <div>
              <Title level={5}>3. 个性化设置</Title>
              <Paragraph>
                登录后点击右上角用户头像，选择"设置"进入个人设置页面，可以配置新闻偏好、语言时区等。
              </Paragraph>
            </div>
            
            <div>
              <Title level={5}>4. 个性化体验</Title>
              <Paragraph>
                系统会根据您的偏好设置和行为记录，在首页为您推荐感兴趣的新闻内容。
              </Paragraph>
            </div>
          </div>
        </Card>

        {/* 底部操作 */}
        <div className="text-center mt-8">
          <Space size="large">
            <Button type="primary" size="large" onClick={() => router.push('/')}>
              返回首页
            </Button>
            {!isAuthenticated && (
              <Button size="large" onClick={() => router.push('/login')}>
                体验登录
              </Button>
            )}
            {isAuthenticated && (
              <Button size="large" onClick={() => router.push('/settings')}>
                个人设置
              </Button>
            )}
          </Space>
        </div>
      </div>
    </div>
  )
}
