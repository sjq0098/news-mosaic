import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Button, 
  message, 
  Divider, 
  Tag, 
  Space,
  InputNumber,
  Row,
  Col
} from 'antd'
import { 
  SettingOutlined, 
  GlobalOutlined, 
  BellOutlined, 
  EyeOutlined,
  TagsOutlined,
  SaveOutlined
} from '@ant-design/icons'
import { userApi } from '../services/api'
import { useAuth } from './AuthContext'

const { Option } = Select
const { TextArea } = Input

interface UserPreferencesData {
  news_interests: string[]
  preferred_categories: string[]
  preferred_sources: string[]
  language: string
  timezone: string
  email_notifications: boolean
  push_notifications: boolean
  items_per_page: number
  theme: string
}

const UserPreferences: React.FC = () => {
  const { user, updateUser } = useAuth()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [preferences, setPreferences] = useState<UserPreferencesData | null>(null)

  // 预定义的新闻分类
  const newsCategories = [
    '科技', '财经', '政治', '体育', '娱乐', '健康', '教育', '环境',
    '国际', '社会', '文化', '军事', '汽车', '房产', '旅游', '美食'
  ]

  // 预定义的新闻来源
  const newsSources = [
    '新华网', '人民网', '央视新闻', '澎湃新闻', '界面新闻', '财新网',
    '36氪', '虎嗅', 'TechCrunch', 'BBC', 'CNN', 'Reuters'
  ]

  // 语言选项
  const languageOptions = [
    { value: 'zh-CN', label: '简体中文' },
    { value: 'zh-TW', label: '繁体中文' },
    { value: 'en-US', label: 'English' },
    { value: 'ja-JP', label: '日本語' },
    { value: 'ko-KR', label: '한국어' }
  ]

  // 时区选项
  const timezoneOptions = [
    { value: 'Asia/Shanghai', label: '北京时间 (UTC+8)' },
    { value: 'Asia/Tokyo', label: '东京时间 (UTC+9)' },
    { value: 'America/New_York', label: '纽约时间 (UTC-5)' },
    { value: 'Europe/London', label: '伦敦时间 (UTC+0)' },
    { value: 'UTC', label: '协调世界时 (UTC)' }
  ]

  // 主题选项
  const themeOptions = [
    { value: 'light', label: '浅色主题' },
    { value: 'dark', label: '深色主题' },
    { value: 'auto', label: '跟随系统' }
  ]

  // 加载用户偏好
  useEffect(() => {
    loadUserPreferences()
  }, [])

  const loadUserPreferences = async () => {
    setLoading(true)
    try {
      const response = await userApi.getUserPreferences()
      const prefs = response.data
      setPreferences(prefs)
      form.setFieldsValue(prefs)
    } catch (error: any) {
      console.error('加载用户偏好失败:', error)
      message.error('加载用户偏好失败')
    } finally {
      setLoading(false)
    }
  }

  // 保存用户偏好
  const handleSave = async (values: UserPreferencesData) => {
    setSaving(true)
    try {
      await userApi.updateUserPreferences(values)
      setPreferences(values)
      
      // 更新用户上下文中的偏好
      if (user) {
        updateUser({ preferences: values })
      }
      
      message.success('偏好设置已保存')
    } catch (error: any) {
      console.error('保存用户偏好失败:', error)
      message.error('保存偏好设置失败')
    } finally {
      setSaving(false)
    }
  }

  // 添加兴趣标签
  const handleAddInterest = (value: string) => {
    if (!value.trim()) return
    
    const currentInterests = form.getFieldValue('news_interests') || []
    if (!currentInterests.includes(value)) {
      form.setFieldsValue({
        news_interests: [...currentInterests, value]
      })
    }
  }

  // 移除兴趣标签
  const handleRemoveInterest = (interest: string) => {
    const currentInterests = form.getFieldValue('news_interests') || []
    form.setFieldsValue({
      news_interests: currentInterests.filter((item: string) => item !== interest)
    })
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card 
        title={
          <Space>
            <SettingOutlined />
            <span>个人偏好设置</span>
          </Space>
        }
        loading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            language: 'zh-CN',
            timezone: 'Asia/Shanghai',
            email_notifications: true,
            push_notifications: true,
            items_per_page: 20,
            theme: 'light',
            news_interests: [],
            preferred_categories: [],
            preferred_sources: []
          }}
        >
          {/* 新闻偏好 */}
          <Card 
            type="inner" 
            title={
              <Space>
                <TagsOutlined />
                <span>新闻偏好</span>
              </Space>
            }
            className="mb-6"
          >
            <Form.Item
              name="news_interests"
              label="感兴趣的关键词"
              help="输入您感兴趣的新闻关键词，用于个性化推荐"
            >
              <Select
                mode="tags"
                placeholder="输入关键词后按回车添加"
                style={{ width: '100%' }}
                tokenSeparators={[',']}
              />
            </Form.Item>

            <Form.Item
              name="preferred_categories"
              label="偏好的新闻分类"
            >
              <Select
                mode="multiple"
                placeholder="选择您感兴趣的新闻分类"
                style={{ width: '100%' }}
              >
                {newsCategories.map(category => (
                  <Option key={category} value={category}>
                    {category}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="preferred_sources"
              label="偏好的新闻来源"
            >
              <Select
                mode="multiple"
                placeholder="选择您信任的新闻来源"
                style={{ width: '100%' }}
              >
                {newsSources.map(source => (
                  <Option key={source} value={source}>
                    {source}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Card>

          {/* 语言和地区 */}
          <Card 
            type="inner" 
            title={
              <Space>
                <GlobalOutlined />
                <span>语言和地区</span>
              </Space>
            }
            className="mb-6"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="language"
                  label="界面语言"
                >
                  <Select>
                    {languageOptions.map(option => (
                      <Option key={option.value} value={option.value}>
                        {option.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="timezone"
                  label="时区设置"
                >
                  <Select>
                    {timezoneOptions.map(option => (
                      <Option key={option.value} value={option.value}>
                        {option.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 通知设置 */}
          <Card 
            type="inner" 
            title={
              <Space>
                <BellOutlined />
                <span>通知设置</span>
              </Space>
            }
            className="mb-6"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="email_notifications"
                  label="邮件通知"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="push_notifications"
                  label="推送通知"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 显示设置 */}
          <Card 
            type="inner" 
            title={
              <Space>
                <EyeOutlined />
                <span>显示设置</span>
              </Space>
            }
            className="mb-6"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="items_per_page"
                  label="每页显示条数"
                  rules={[
                    { type: 'number', min: 10, max: 100, message: '请输入10-100之间的数字' }
                  ]}
                >
                  <InputNumber min={10} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="theme"
                  label="主题设置"
                >
                  <Select>
                    {themeOptions.map(option => (
                      <Option key={option.value} value={option.value}>
                        {option.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 保存按钮 */}
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={saving}
              icon={<SaveOutlined />}
              size="large"
            >
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default UserPreferences
