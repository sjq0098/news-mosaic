import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { Form, Input, Button, Card, message, Space, Progress, Typography, Row, Col } from 'antd'
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  BarChartOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  StarOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons'
import Link from 'next/link'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text } = Typography

interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  nickname?: string
}

export default function RegisterPage() {
  const router = useRouter()
  const { register, isAuthenticated, isLoading } = useAuth()
  const [registerForm] = Form.useForm()
  const [registerLoading, setRegisterLoading] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [passwordStrengthText, setPasswordStrengthText] = useState('')

  // 检查是否已登录
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  // 密码强度检查
  const checkPasswordStrength = (password: string) => {
    let strength = 0
    let text = ''

    if (password.length >= 6) strength += 20
    if (password.length >= 8) strength += 10
    if (/[a-z]/.test(password)) strength += 20
    if (/[A-Z]/.test(password)) strength += 20
    if (/[0-9]/.test(password)) strength += 15
    if (/[^A-Za-z0-9]/.test(password)) strength += 15

    if (strength < 30) {
      text = '弱'
    } else if (strength < 60) {
      text = '中等'
    } else if (strength < 90) {
      text = '强'
    } else {
      text = '很强'
    }

    setPasswordStrength(strength)
    setPasswordStrengthText(text)
  }

  // 处理注册
  const handleRegister = async (values: RegisterForm) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    setRegisterLoading(true)
    try {
      const success = await register({
        username: values.username,
        email: values.email,
        password: values.password,
        nickname: values.nickname
      })

      if (success) {
        message.success('注册成功！正在跳转到登录页面...')
        setTimeout(() => {
          router.push('/login')
        }, 1500)
      }
    } catch (error: any) {
      console.error('注册错误:', error)
      message.error('注册失败，请检查网络连接')
    } finally {
      setRegisterLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* 几何图案 */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-10 left-10 w-32 h-32 border border-blue-400 rounded-full animate-pulse"></div>
          <div className="absolute top-32 right-20 w-24 h-24 border border-purple-400 rounded-lg rotate-45 animate-bounce"></div>
          <div className="absolute bottom-20 left-20 w-40 h-40 border border-indigo-400 rounded-full animate-pulse"></div>
          <div className="absolute bottom-32 right-32 w-28 h-28 border border-cyan-400 rounded-lg rotate-12 animate-bounce"></div>

          {/* 网格背景 */}
          <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(99, 102, 241, 0.1)" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
      </div>

      <div className="relative z-10 min-h-screen flex">
        <Row className="w-full">
          {/* 左侧品牌介绍 */}
          <Col xs={0} lg={13} className="flex items-center justify-center px-16 py-12">
            <div className="max-w-2xl text-white">
              <div className="mb-12">
                <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-green-500 to-blue-600 rounded-3xl mb-8 shadow-2xl animate-float">
                  <BarChartOutlined className="text-white text-4xl" />
                </div>
                <Title level={1} className="text-white mb-6 text-6xl font-bold tracking-tight leading-tight">
                  加入 News Mosaic
                </Title>
                <Title level={3} className="text-blue-200 mb-4 text-2xl font-normal">
                  开启您的智能新闻分析之旅
                </Title>
                <Text className="text-blue-100 text-xl leading-relaxed block">
                  体验AI驱动的新闻分析，让信息更有价值
                </Text>
              </div>

              {/* 特色功能 */}
              <div className="space-y-8">
                <div className="flex items-start space-x-5">
                  <div className="flex-shrink-0 w-14 h-14 bg-blue-500/20 rounded-2xl flex items-center justify-center border border-blue-400/30">
                    <ThunderboltOutlined className="text-blue-400 text-2xl" />
                  </div>
                  <div className="pt-1">
                    <h3 className="text-white font-bold text-xl mb-2">实时新闻聚合</h3>
                    <p className="text-blue-200 text-base leading-relaxed">多源新闻实时抓取，一站式获取全球资讯</p>
                  </div>
                </div>

                <div className="flex items-start space-x-5">
                  <div className="flex-shrink-0 w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center border border-purple-400/30">
                    <BarChartOutlined className="text-purple-400 text-2xl" />
                  </div>
                  <div className="pt-1">
                    <h3 className="text-white font-bold text-xl mb-2">AI智能分析</h3>
                    <p className="text-blue-200 text-base leading-relaxed">通义千问驱动，深度解读新闻内容</p>
                  </div>
                </div>

                <div className="flex items-start space-x-5">
                  <div className="flex-shrink-0 w-14 h-14 bg-indigo-500/20 rounded-2xl flex items-center justify-center border border-indigo-400/30">
                    <GlobalOutlined className="text-indigo-400 text-2xl" />
                  </div>
                  <div className="pt-1">
                    <h3 className="text-white font-bold text-xl mb-2">个性化推荐</h3>
                    <p className="text-blue-200 text-base leading-relaxed">基于用户偏好的智能内容推荐</p>
                  </div>
                </div>
              </div>

              {/* 用户评价 */}
              <div className="mt-16 p-8 bg-white/10 backdrop-blur-sm rounded-3xl border border-white/20 shadow-2xl">
                <div className="flex items-center space-x-3 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <StarOutlined key={i} className="text-yellow-400 text-lg" />
                  ))}
                  <span className="text-white font-bold text-lg">4.9/5</span>
                </div>
                <p className="text-blue-100 italic text-lg leading-relaxed mb-3">
                  "注册后立即体验到了AI分析的强大功能，新闻理解效率提升了很多！"
                </p>
                <p className="text-blue-300 text-base font-medium">— 来自新用户的真实反馈</p>
              </div>

              {/* 安全认证 */}
              <div className="mt-10 flex items-center space-x-5">
                <div className="flex-shrink-0 w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center border border-green-400/30">
                  <SafetyCertificateOutlined className="text-green-400 text-2xl" />
                </div>
                <div>
                  <p className="text-white font-bold text-lg">数据安全保障</p>
                  <p className="text-blue-200 text-base">企业级加密，隐私保护</p>
                </div>
              </div>
            </div>
          </Col>

          {/* 右侧注册表单 */}
          <Col xs={24} lg={11} className="flex items-center justify-center px-12 py-16">
            <div className="w-full max-w-lg">
              {/* 注册卡片 */}
              <Card
                className="shadow-2xl border-0 rounded-3xl overflow-hidden backdrop-blur-lg bg-white/95"
                bodyStyle={{ padding: 0 }}
              >
                <div className="px-12 py-16">
                  {/* 注册标题 */}
                  <div className="text-center mb-10">
                    <Title level={2} className="mb-4 text-3xl font-bold text-gray-800">
                      创建新账户
                    </Title>
                    <Text className="text-gray-600 text-lg">
                      加入我们，开始您的智能新闻分析之旅
                    </Text>
                  </div>

                  {/* 注册表单 */}
                  <Form
                    form={registerForm}
                    name="register"
                    onFinish={handleRegister}
                    layout="vertical"
                    size="large"
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          label={<span className="text-gray-700 font-semibold text-base">用户名</span>}
                          name="username"
                          className="mb-6"
                          rules={[
                            { required: true, message: '请输入用户名' },
                            { min: 3, max: 50, message: '用户名长度为3-50个字符' },
                            { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
                          ]}
                        >
                          <Input
                            prefix={<UserOutlined className="text-gray-400" />}
                            placeholder="请输入用户名"
                            className="rounded-2xl h-14 border-2 hover:border-blue-400 focus:border-blue-500 transition-all duration-300"
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          label={<span className="text-gray-700 font-semibold text-base">昵称（可选）</span>}
                          name="nickname"
                          className="mb-6"
                          rules={[
                            { max: 100, message: '昵称最多100个字符' }
                          ]}
                        >
                          <Input
                            prefix={<UserOutlined className="text-gray-400" />}
                            placeholder="请输入昵称"
                            className="rounded-2xl h-14 border-2 hover:border-blue-400 focus:border-blue-500 transition-all duration-300"
                          />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      label={<span className="text-gray-700 font-semibold text-base">邮箱地址</span>}
                      name="email"
                      className="mb-6"
                      rules={[
                        { required: true, message: '请输入邮箱地址' },
                        { type: 'email', message: '请输入有效的邮箱地址' }
                      ]}
                    >
                      <Input
                        prefix={<MailOutlined className="text-gray-400" />}
                        placeholder="请输入邮箱地址"
                        className="rounded-2xl h-14 border-2 hover:border-blue-400 focus:border-blue-500 transition-all duration-300"
                      />
                    </Form.Item>

                    <Form.Item
                      label={<span className="text-gray-700 font-semibold text-base">密码</span>}
                      name="password"
                      className="mb-6"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 6, max: 128, message: '密码长度为6-128个字符' }
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined className="text-gray-400" />}
                        placeholder="请输入密码"
                        className="rounded-2xl h-14 border-2 hover:border-blue-400 focus:border-blue-500 transition-all duration-300"
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                        onChange={(e) => checkPasswordStrength(e.target.value)}
                      />
                      {passwordStrength > 0 && (
                        <div className="mt-3">
                          <div className="flex justify-between items-center mb-2">
                            <Text className="text-sm text-gray-600">密码强度</Text>
                            <Text className={`text-sm font-medium ${
                              passwordStrength < 30 ? 'text-red-500' :
                              passwordStrength < 60 ? 'text-orange-500' :
                              passwordStrength < 90 ? 'text-blue-500' : 'text-green-500'
                            }`}>
                              {passwordStrengthText}
                            </Text>
                          </div>
                          <Progress 
                            percent={passwordStrength} 
                            showInfo={false}
                            strokeColor={
                              passwordStrength < 30 ? '#ef4444' :
                              passwordStrength < 60 ? '#f97316' :
                              passwordStrength < 90 ? '#3b82f6' : '#10b981'
                            }
                            size="small"
                          />
                        </div>
                      )}
                    </Form.Item>

                    <Form.Item
                      label={<span className="text-gray-700 font-semibold text-base">确认密码</span>}
                      name="confirmPassword"
                      className="mb-8"
                      dependencies={['password']}
                      rules={[
                        { required: true, message: '请确认密码' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('password') === value) {
                              return Promise.resolve()
                            }
                            return Promise.reject(new Error('两次输入的密码不一致'))
                          },
                        }),
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined className="text-gray-400" />}
                        placeholder="请再次输入密码"
                        className="rounded-2xl h-14 border-2 hover:border-blue-400 focus:border-blue-500 transition-all duration-300"
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>

                    <Form.Item className="mb-8">
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={registerLoading}
                        className="w-full h-16 rounded-2xl bg-gradient-to-r from-green-600 to-blue-600 border-0 text-white font-bold text-xl hover:from-green-700 hover:to-blue-700 transition-all duration-300 shadow-xl hover:shadow-2xl hover:scale-105"
                      >
                        {registerLoading ? '注册中...' : '开始分析 →'}
                      </Button>
                    </Form.Item>
                  </Form>

                  {/* 服务条款 */}
                  <div className="text-center text-sm text-gray-500 mb-6">
                    注册即表示您同意我们的
                    <Button type="link" className="p-0 text-blue-600 text-sm">服务条款</Button>
                    和
                    <Button type="link" className="p-0 text-blue-600 text-sm">隐私政策</Button>
                  </div>

                  {/* 登录链接 */}
                  <div className="text-center">
                    <Text className="text-gray-600 text-base">已有账号？</Text>
                    <Button
                      type="link"
                      onClick={() => router.push('/login')}
                      className="p-0 ml-2 text-blue-600 hover:text-blue-700 font-bold text-base"
                    >
                      立即登录 →
                    </Button>
                  </div>
                </div>
              </Card>

              {/* 底部链接 */}
              <div className="text-center mt-12">
                <Space split={<span className="text-blue-300 mx-2">•</span>} className="text-blue-200 text-base">
                  <Link href="/" className="hover:text-white transition-colors font-medium">
                    返回首页
                  </Link>
                  <span className="hover:text-white transition-colors cursor-pointer font-medium">关于我们</span>
                  <span className="hover:text-white transition-colors cursor-pointer font-medium">帮助中心</span>
                  <span className="hover:text-white transition-colors cursor-pointer font-medium">联系我们</span>
                </Space>
              </div>

              {/* 版权信息 */}
              <div className="text-center mt-6 text-blue-300 text-base">
                © 2025 News Mosaic. 保留所有权利.
              </div>
            </div>
          </Col>
        </Row>
      </div>

      <style jsx global>{`
        /* 自定义输入框样式 */
        .ant-input-affix-wrapper:focus,
        .ant-input-affix-wrapper-focused {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        /* 自定义按钮悬停效果 */
        .ant-btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 30px rgba(59, 130, 246, 0.4);
        }
        
        /* 动画效果 */
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        
        /* 背景动画 */
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.3; }
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}
