import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { Form, Input, Button, Card, message, Space, Typography, Row, Col } from 'antd'
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  CheckCircleOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  GlobalOutlined,
  StarOutlined
} from '@ant-design/icons'
import Link from 'next/link'
import { userApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text } = Typography

interface LoginForm {
  username: string
  password: string
}

export default function LoginPage() {
  const router = useRouter()
  const { login, isAuthenticated, isLoading } = useAuth()
  const [loginForm] = Form.useForm()
  const [loginLoading, setLoginLoading] = useState(false)

  // 检查是否已登录
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  // 处理登录
  const handleLogin = async (values: LoginForm) => {
    setLoginLoading(true)
    try {
      const success = await login(values.username, values.password)

      if (success) {
        // 跳转到首页或之前的页面
        const redirect = router.query.redirect as string
        router.push(redirect || '/')
      }
    } catch (error: any) {
      console.error('登录错误:', error)
      message.error('登录失败，请检查网络连接')
    } finally {
      setLoginLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 马卡龙风格背景装饰 */}
      <div className="absolute inset-0">
        {/* 柔和几何图案 */}
        <div className="absolute inset-0 opacity-30">
          {/* 浮动的马卡龙色彩圆形 */}
          <div className="absolute top-20 left-16 w-40 h-40 bg-macaron-pink/20 rounded-full blur-xl animate-gentle-pulse"></div>
          <div className="absolute top-40 right-24 w-32 h-32 bg-macaron-mint/20 rounded-full blur-lg animate-bounce"></div>
          <div className="absolute bottom-32 left-32 w-48 h-48 bg-macaron-lavender/20 rounded-full blur-2xl animate-gentle-pulse"></div>
          <div className="absolute bottom-20 right-20 w-36 h-36 bg-macaron-yellow/20 rounded-full blur-lg animate-bounce"></div>

          {/* 中间层装饰 */}
          <div className="absolute top-1/3 left-1/4 w-24 h-24 bg-primary-200/30 rounded-2xl rotate-12 animate-gentle-pulse"></div>
          <div className="absolute bottom-1/3 right-1/4 w-28 h-28 bg-macaron-mint/30 rounded-3xl rotate-45 animate-bounce"></div>

          {/* 柔和网格背景 */}
          <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="macaronGrid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(168, 216, 240, 0.08)" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#macaronGrid)" />
          </svg>
        </div>
      </div>

      {/* 顶部品牌标题区域 - 真正居中布局 */}
      <div className="relative z-10 w-full absolute top-0 left-0 right-0">
        <div className="flex justify-center items-center w-full pt-12 pb-8">
          <div className="text-center">
            {/* 品牌图标 - 马卡龙风格 */}
            <div className="inline-flex items-center justify-center w-28 h-28 bg-gradient-to-br from-primary-200 to-primary-300 rounded-3xl mb-12 shadow-xl animate-gentle-float backdrop-blur-sm border border-white/20">
              <BarChartOutlined className="text-primary-700 text-5xl" />
            </div>

            {/* 品牌标题 - 大幅增大字号和样式 */}
            <Title level={1} className="brand-title mb-8 leading-none tracking-tight" style={{ fontSize: '6rem', lineHeight: '1' }}>
              News Mosaic
            </Title>
            <Title level={2} className="brand-subtitle mb-10 font-light" style={{ fontSize: '3rem', lineHeight: '1.2' }}>
              智能新闻分析平台
            </Title>
            <Text className="brand-description block max-w-4xl mx-auto leading-relaxed" style={{ fontSize: '1.5rem', lineHeight: '1.6' }}>
              登录您的账户，继续探索全球资讯世界
            </Text>
          </div>
        </div>
      </div>

      {/* 主要内容区域 - 添加顶部间距来避免与标题重叠 */}
      <div className="relative z-10 pt-96">
        <Row className="w-full">
          {/* 左侧功能介绍 */}
          <Col xs={0} lg={13} className="px-20 pb-20">
            <div className="max-w-2xl mx-auto">
              {/* 特色功能卡片 - 重构为卡片式设计 */}
              <div className="space-y-8 mb-16">
                {/* 实时新闻聚合 */}
                <div className="feature-card macaron-hover">
                  <div className="flex items-start space-x-6">
                    <div className="feature-icon-wrapper bg-macaron-mint">
                      <ThunderboltOutlined className="text-gray-700 text-2xl" />
                    </div>
                    <div className="pt-1">
                      <h3 className="font-subheading text-heading-sm text-gray-800 mb-3">实时新闻聚合</h3>
                      <p className="font-body text-body-lg text-gray-600 leading-relaxed">多源新闻实时抓取，一站式获取全球资讯</p>
                    </div>
                  </div>
                </div>

                {/* AI智能分析 */}
                <div className="feature-card macaron-hover">
                  <div className="flex items-start space-x-6">
                    <div className="feature-icon-wrapper bg-macaron-lavender">
                      <BarChartOutlined className="text-gray-700 text-2xl" />
                    </div>
                    <div className="pt-1">
                      <h3 className="font-subheading text-heading-sm text-gray-800 mb-3">AI智能分析</h3>
                      <p className="font-body text-body-lg text-gray-600 leading-relaxed">通义千问驱动，深度解读新闻内容</p>
                    </div>
                  </div>
                </div>

                {/* 个性化推荐 */}
                <div className="feature-card macaron-hover">
                  <div className="flex items-start space-x-6">
                    <div className="feature-icon-wrapper bg-macaron-pink">
                      <GlobalOutlined className="text-gray-700 text-2xl" />
                    </div>
                    <div className="pt-1">
                      <h3 className="font-subheading text-heading-sm text-gray-800 mb-3">个性化推荐</h3>
                      <p className="font-body text-body-lg text-gray-600 leading-relaxed">基于用户偏好的智能内容推荐</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 用户评价卡片 - 马卡龙风格 */}
              <div className="testimonial-card mb-12">
                <div className="flex items-center space-x-4 mb-6">
                  {[...Array(5)].map((_, i) => (
                    <StarOutlined key={i} className="text-macaron-yellow text-2xl" />
                  ))}
                  <span className="font-heading text-heading-sm text-gray-800">4.9/5</span>
                </div>
                <p className="font-body text-body-xl text-gray-700 italic leading-relaxed mb-4">
                  "News Mosaic让我能够快速了解全球新闻动态，AI分析功能特别实用！"
                </p>
                <p className="font-caption text-body-lg text-gray-500">— 来自1000+用户的真实评价</p>
              </div>

              {/* 安全认证 - 马卡龙风格 */}
              <div className="security-badge flex items-center space-x-6">
                <div className="flex-shrink-0 w-14 h-14 bg-macaron-mint rounded-xl flex items-center justify-center shadow-md">
                  <SafetyCertificateOutlined className="text-gray-700 text-2xl" />
                </div>
                <div>
                  <p className="font-subheading text-body-lg text-gray-800">数据安全保障</p>
                  <p className="font-body text-body-md text-gray-600">企业级加密，隐私保护</p>
                </div>
              </div>
            </div>
          </Col>

          {/* 右侧登录表单 - 添加粘性定位 */}
          <Col xs={24} lg={11} className="px-16">
            <div className="sticky top-8 w-full max-w-xl mx-auto">
              {/* 登录卡片 - 玻璃拟态优化 */}
              <Card
                className="auth-card shadow-2xl border-0"
                bodyStyle={{ padding: 0 }}
              >
                <div className="px-12 py-16">
                  {/* 登录标题 - 优化字体层级和间距 */}
                  <div className="text-center mb-12">
                    <Title level={2} className="font-heading text-heading-xl text-gray-800 mb-6">
                      欢迎回来
                    </Title>
                    <Text className="font-body text-body-lg text-gray-600">
                      登录您的账户，继续探索新闻世界
                    </Text>
                  </div>

                  {/* 登录表单 - 增强间距和美感 */}
                  <Form
                    form={loginForm}
                    name="login"
                    onFinish={handleLogin}
                    layout="vertical"
                    size="large"
                  >
                    <Form.Item
                      label={<span className="font-caption text-body-md text-gray-700">用户名或邮箱</span>}
                      name="username"
                      className="mb-8"
                      rules={[
                        { required: true, message: '请输入用户名或邮箱' },
                        { min: 3, message: '用户名至少3个字符' }
                      ]}
                    >
                      <Input
                        prefix={<UserOutlined className="text-gray-400" />}
                        placeholder="请输入用户名或邮箱"
                        className="auth-input font-body"
                      />
                    </Form.Item>

                    <Form.Item
                      label={<span className="font-caption text-body-md text-gray-700">密码</span>}
                      name="password"
                      className="mb-12"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 6, message: '密码至少6个字符' }
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined className="text-gray-400" />}
                        placeholder="请输入密码"
                        className="auth-input font-body"
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>

                    <Form.Item className="mb-8">
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loginLoading}
                        className="auth-button w-full bg-gradient-to-r from-primary-300 to-primary-400 border-0 text-gray-800 font-subheading hover:from-primary-400 hover:to-primary-500 macaron-button"
                      >
                        {loginLoading ? '登录中...' : '立即登录'}
                      </Button>
                    </Form.Item>
                  </Form>

                  {/* 注册链接 - 优化样式 */}
                  <div className="text-center">
                    <Text className="font-body text-body-md text-gray-600">还没有账号？</Text>
                    <Button
                      type="link"
                      onClick={() => router.push('/register')}
                      className="p-0 ml-2 text-primary-600 hover:text-primary-700 font-subheading text-body-md"
                    >
                      立即注册 →
                    </Button>
                  </div>
                </div>
              </Card>

              {/* 底部链接 - 优化间距和字体 */}
              <div className="text-center mt-8">
                <Space split={<span className="text-gray-400 mx-2">•</span>} className="text-gray-600 font-body text-body-sm">
                  <Link href="/" className="hover:text-gray-800 transition-colors">
                    返回首页
                  </Link>
                  <span className="hover:text-gray-800 transition-colors cursor-pointer">关于我们</span>
                  <span className="hover:text-gray-800 transition-colors cursor-pointer">帮助中心</span>
                  <span className="hover:text-gray-800 transition-colors cursor-pointer">联系我们</span>
                </Space>
              </div>

              {/* 版权信息 - 优化字体 */}
              <div className="text-center mt-4 font-caption text-body-xs text-gray-500">
                © 2025 News Mosaic. 保留所有权利.
              </div>
            </div>
          </Col>
        </Row>
      </div>

      <style jsx global>{`
        /* 自定义样式补充 */
        .ant-form-item-label > label {
          font-weight: 500;
          color: #4A5568;
        }

        .ant-input-affix-wrapper {
          border-radius: 16px !important;
          border-width: 2px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .ant-input-affix-wrapper:hover {
          border-color: var(--primary-light) !important;
          background: rgba(255, 255, 255, 0.9);
        }

        .ant-input-affix-wrapper:focus,
        .ant-input-affix-wrapper-focused {
          border-color: var(--primary-color) !important;
          box-shadow: 0 0 0 4px rgba(168, 216, 240, 0.15) !important;
          transform: translateY(-1px);
        }

        .ant-btn-primary {
          border-radius: 16px !important;
          font-weight: 600 !important;
          font-size: 1rem !important;
          height: 3rem !important;
          box-shadow: 0 6px 16px rgba(168, 216, 240, 0.3) !important;
        }

        .ant-btn-primary:hover {
          transform: translateY(-2px) !important;
          box-shadow: 0 8px 24px rgba(168, 216, 240, 0.4) !important;
        }

        .ant-btn-primary:active {
          transform: translateY(-1px) !important;
        }

        .ant-btn-link {
          height: auto !important;
          padding: 0 !important;
          border: none !important;
          transition: all 0.2s ease !important;
        }

        .ant-btn-link:hover {
          text-decoration: underline !important;
          transform: translateX(2px) !important;
        }

        /* 增强品牌标题样式 */
        .brand-title {
          background: linear-gradient(135deg, #1a202c 0%, #2d3748 30%, #4a5568 60%, #2d3748 100%);
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          font-weight: 900;
          letter-spacing: -0.04em;
          line-height: 0.9;
          text-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
          position: relative;
        }

        .brand-title::after {
          content: '';
          position: absolute;
          bottom: -8px;
          left: 50%;
          transform: translateX(-50%);
          width: 120px;
          height: 3px;
          background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
          border-radius: 2px;
        }

        .brand-subtitle {
          color: #4A5568;
          font-weight: 300;
          letter-spacing: -0.02em;
          margin-top: var(--spacing-lg);
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .brand-description {
          color: #718096;
          font-weight: 400;
          letter-spacing: 0.01em;
          margin-top: var(--spacing-lg);
          line-height: 1.7;
        }

        /* 响应式字体调整 */
        @media (max-width: 768px) {
          .brand-title {
            font-size: 3.5rem !important;
            letter-spacing: -0.03em;
          }
          
          .brand-subtitle {
            font-size: 1.5rem !important;
          }
          
          .brand-description {
            font-size: 1rem !important;
          }
        }

        @media (max-width: 480px) {
          .brand-title {
            font-size: 2.5rem !important;
            letter-spacing: -0.02em;
          }
          
          .brand-subtitle {
            font-size: 1.25rem !important;
          }
        }

        /* 粘性定位样式 */
        .sticky {
          position: sticky;
          top: 2rem;
        }

        /* 响应式调整 */
        @media (max-width: 1024px) {
          .sticky {
            position: static;
          }
        }

        /* 小字体尺寸 */
        .text-body-xs { font-size: 0.625rem; }
      `}</style>
    </div>
  )
}
