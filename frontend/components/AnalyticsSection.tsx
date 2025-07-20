import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Progress, 
  Select, 
  DatePicker, 
  Button,
  Space,
  Spin,
  message
} from 'antd'
import { 
  TrophyOutlined, 
  RiseOutlined, 
  FallOutlined,
  EyeOutlined,
  HeartOutlined,
  MessageOutlined,
  ReloadOutlined,
  DownloadOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import { Line, Column, Pie, Area } from '@ant-design/plots'
import dayjs from 'dayjs'
import { analyticsApi } from '../services/api'

const { Option } = Select
const { RangePicker } = DatePicker

interface AnalyticsData {
  sentimentStats: {
    positive: number
    negative: number
    neutral: number
    total: number
  }
  categoryStats: Array<{
    category: string
    count: number
    percentage: number
  }>
  trendData: Array<{
    date: string
    positive: number
    negative: number
    neutral: number
    total: number
  }>
  topNews: Array<{
    title: string
    views: number
    sentiment: string
    category: string
  }>
  keywordCloud: Array<{
    text: string
    value: number
  }>
}

export default function AnalyticsSection() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(7, 'day'),
    dayjs()
  ])
  const [category, setCategory] = useState('all')

  // 获取分析数据
  const fetchAnalyticsData = async () => {
    setLoading(true)
    try {
      const [start, end] = timeRange
      const response = await analyticsApi.getSentimentStats({
        start_date: start.format('YYYY-MM-DD'),
        end_date: end.format('YYYY-MM-DD'),
        category: category === 'all' ? undefined : category
      })

      if (response.data.success) {
        setData(response.data.data)
      } else {
        // 使用模拟数据
        setData(generateMockData())
      }
    } catch (error) {
      console.error('Analytics error:', error)
      // 使用模拟数据
      setData(generateMockData())
    } finally {
      setLoading(false)
    }
  }

  // 生成模拟数据
  const generateMockData = (): AnalyticsData => {
    const days = timeRange[1].diff(timeRange[0], 'day') + 1
    
    return {
      sentimentStats: {
        positive: 456,
        negative: 234,
        neutral: 567,
        total: 1257
      },
      categoryStats: [
        { category: '科技', count: 345, percentage: 27.4 },
        { category: '财经', count: 289, percentage: 23.0 },
        { category: '政治', count: 234, percentage: 18.6 },
        { category: '体育', count: 198, percentage: 15.7 },
        { category: '娱乐', count: 191, percentage: 15.2 }
      ],
      trendData: Array.from({ length: days }, (_, index) => {
        const date = timeRange[0].add(index, 'day')
        return {
          date: date.format('MM-DD'),
          positive: Math.floor(Math.random() * 50) + 20,
          negative: Math.floor(Math.random() * 30) + 10,
          neutral: Math.floor(Math.random() * 40) + 15,
          total: Math.floor(Math.random() * 120) + 45
        }
      }),
      topNews: [
        { title: 'AI技术突破性进展引发关注', views: 12450, sentiment: 'positive', category: '科技' },
        { title: '经济数据显示稳定增长趋势', views: 9876, sentiment: 'positive', category: '财经' },
        { title: '新政策将影响多个行业发展', views: 8765, sentiment: 'neutral', category: '政治' },
        { title: '体育赛事精彩瞬间回顾', views: 7654, sentiment: 'positive', category: '体育' },
        { title: '娱乐圈最新动态汇总', views: 6543, sentiment: 'neutral', category: '娱乐' }
      ],
      keywordCloud: [
        { text: '人工智能', value: 120 },
        { text: '经济发展', value: 95 },
        { text: '科技创新', value: 87 },
        { text: '政策解读', value: 76 },
        { text: '市场分析', value: 65 }
      ]
    }
  }

  useEffect(() => {
    fetchAnalyticsData()
  }, [timeRange, category])

  // 情感趋势图配置
  const trendConfig = {
    data: data?.trendData || [],
    xField: 'date',
    yField: 'total',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: ['#52c41a', '#ff4d4f', '#1890ff'],
  }

  // 分类分布图配置
  const categoryConfig = {
    data: data?.categoryStats || [],
    xField: 'category',
    yField: 'count',
    color: ({ category }: any) => {
      const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
      const index = ['科技', '财经', '政治', '体育', '娱乐'].indexOf(category)
      return colors[index] || '#6366f1'
    },
    columnWidthRatio: 0.6,
    animation: {
      appear: {
        animation: 'grow-in-xy',
        duration: 1000,
      },
    },
  }

  // 情感分布饼图配置
  const sentimentConfig = {
    appendPadding: 10,
    data: data ? [
      { type: '正面', value: data.sentimentStats.positive },
      { type: '负面', value: data.sentimentStats.negative },
      { type: '中性', value: data.sentimentStats.neutral },
    ] : [],
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    color: ['#10b981', '#ef4444', '#6366f1'],
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [{ type: 'pie-legend-active' }, { type: 'element-active' }],
  }

  return (
    <div className="space-y-8">
      {/* 欢迎横幅 */}
      <div className="glass-card p-8 text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-full flex items-center justify-center mr-4">
            <BarChartOutlined className="text-white text-2xl" />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
            智能数据分析
          </h2>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          全方位新闻数据分析，深度洞察舆情趋势和热点话题
        </p>
      </div>

      {/* 控制面板 */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-100 to-red-100 dark:from-orange-800 dark:to-red-800 rounded-full flex items-center justify-center">
              <ThunderboltOutlined className="text-orange-600 dark:text-orange-400 text-lg" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white m-0">
                数据分析控制台
              </h3>
              <p className="text-gray-500 mt-1 m-0">
                实时监控新闻情感和趋势变化
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <RangePicker
              value={timeRange}
              onChange={(dates) => dates && setTimeRange(dates)}
              format="YYYY-MM-DD"
              className="modern-input"
            />
            <Select
              value={category}
              onChange={setCategory}
              className="w-32"
              placeholder="选择分类"
            >
              <Option value="all">🌟 全部分类</Option>
              <Option value="technology">🔬 科技</Option>
              <Option value="business">💼 财经</Option>
              <Option value="politics">🏛️ 政治</Option>
              <Option value="sports">⚽ 体育</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchAnalyticsData}
              loading={loading}
              className="glass-card border-0 hover:scale-105 transition-all duration-300"
            >
              刷新数据
            </Button>
            <Button
              icon={<DownloadOutlined />}
              type="primary"
              className="modern-button hover:scale-105 transition-all duration-300"
            >
              导出报告
            </Button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-card p-16 text-center">
          <div className="flex flex-col items-center space-y-4">
            <div className="loading-pulse">
              <BarChartOutlined className="text-6xl text-orange-500" />
            </div>
            <Spin size="large" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">正在分析数据...</p>
          </div>
        </div>
      ) : (
        <>
          {/* 概览统计 */}
          <Row gutter={[24, 24]}>
            <Col xs={24} sm={12} lg={6}>
              <div className="glass-card p-6 text-center hover:scale-105 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrophyOutlined className="text-white text-xl" />
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  {data?.sentimentStats.total || 0}
                </div>
                <div className="text-gray-500 font-medium">总新闻数</div>
              </div>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div className="glass-card p-6 text-center hover:scale-105 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <RiseOutlined className="text-white text-xl" />
                </div>
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {data?.sentimentStats.positive || 0}
                </div>
                <div className="text-gray-500 font-medium">
                  正面新闻 ({data ? ((data.sentimentStats.positive / data.sentimentStats.total) * 100).toFixed(1) : 0}%)
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div className="glass-card p-6 text-center hover:scale-105 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FallOutlined className="text-white text-xl" />
                </div>
                <div className="text-3xl font-bold text-red-600 mb-2">
                  {data?.sentimentStats.negative || 0}
                </div>
                <div className="text-gray-500 font-medium">
                  负面新闻 ({data ? ((data.sentimentStats.negative / data.sentimentStats.total) * 100).toFixed(1) : 0}%)
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <div className="glass-card p-6 text-center hover:scale-105 transition-all duration-300">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <LineChartOutlined className="text-white text-xl" />
                </div>
                <div className="text-3xl font-bold text-purple-600 mb-2">
                  {data?.sentimentStats.neutral || 0}
                </div>
                <div className="text-gray-500 font-medium">
                  中性新闻 ({data ? ((data.sentimentStats.neutral / data.sentimentStats.total) * 100).toFixed(1) : 0}%)
                </div>
              </div>
            </Col>
          </Row>

          {/* 图表展示 */}
          <Row gutter={[24, 24]}>
            {/* 情感趋势 */}
            <Col xs={24} lg={16}>
              <div className="glass-card p-6 hover:scale-[1.02] transition-all duration-300">
                <div className="flex items-center mb-6">
                  <LineChartOutlined className="text-blue-500 text-xl mr-3" />
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white m-0">情感趋势分析</h3>
                </div>
                <Area
                  {...{
                    data: data?.trendData.flatMap(item => [
                      { date: item.date, value: item.positive, type: '正面' },
                      { date: item.date, value: item.negative, type: '负面' },
                      { date: item.date, value: item.neutral, type: '中性' }
                    ]) || [],
                    xField: 'date',
                    yField: 'value',
                    seriesField: 'type',
                    isStack: true,
                    smooth: true,
                    color: ['#10b981', '#ef4444', '#6366f1'],
                    animation: {
                      appear: {
                        animation: 'wave-in',
                        duration: 1500,
                      },
                    },
                  }}
                  height={300}
                />
              </div>
            </Col>

            {/* 情感分布 */}
            <Col xs={24} lg={8}>
              <div className="glass-card p-6 hover:scale-[1.02] transition-all duration-300">
                <div className="flex items-center mb-6">
                  <PieChartOutlined className="text-purple-500 text-xl mr-3" />
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white m-0">情感分布</h3>
                </div>
                <Pie {...sentimentConfig} height={300} />
              </div>
            </Col>
          </Row>

          <Row gutter={[24, 24]}>
            {/* 分类统计 */}
            <Col xs={24} lg={12}>
              <div className="glass-card p-6 hover:scale-[1.02] transition-all duration-300">
                <div className="flex items-center mb-6">
                  <BarChartOutlined className="text-orange-500 text-xl mr-3" />
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white m-0">分类统计</h3>
                </div>
                <Column {...categoryConfig} height={300} />
              </div>
            </Col>

            {/* 热门新闻 */}
            <Col xs={24} lg={12}>
              <div className="glass-card p-6 hover:scale-[1.02] transition-all duration-300">
                <div className="flex items-center mb-6">
                  <TrophyOutlined className="text-yellow-500 text-xl mr-3" />
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white m-0">热门新闻排行</h3>
                </div>
                <div className="space-y-4">
                  {data?.topNews.map((news, index) => (
                    <div key={index} className="glass-card p-4 hover:scale-105 transition-all duration-300">
                      <div className="flex items-start space-x-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                          index === 0 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' :
                          index === 1 ? 'bg-gradient-to-r from-gray-400 to-gray-500' :
                          index === 2 ? 'bg-gradient-to-r from-amber-600 to-amber-700' :
                          'bg-gradient-to-r from-blue-400 to-blue-500'
                        }`}>
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 dark:text-white line-clamp-1 mb-2">
                            {news.title}
                          </h4>
                          <div className="flex items-center space-x-4 text-sm">
                            <span className="flex items-center text-gray-500">
                              <EyeOutlined className="mr-1" />
                              {news.views.toLocaleString()}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              news.sentiment === 'positive' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                              news.sentiment === 'negative' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                              'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                            }`}>
                              {news.sentiment === 'positive' ? '😊 正面' : 
                               news.sentiment === 'negative' ? '😔 负面' : '😐 中性'}
                            </span>
                            <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full text-xs font-medium">
                              {news.category}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Col>
          </Row>

          {/* 详细分析 */}
          <div className="glass-card p-8">
            <div className="flex items-center mb-8">
              <PieChartOutlined className="text-green-500 text-2xl mr-4" />
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white m-0">情感分析详情</h3>
            </div>
            <Row gutter={[32, 32]}>
              <Col xs={24} sm={8}>
                <div className="text-center p-6 glass-card hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-green-600 mb-4">
                    {data ? ((data.sentimentStats.positive / data.sentimentStats.total) * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-gray-500 mb-6 font-medium">正面情感占比</div>
                  <Progress
                    type="circle"
                    percent={data ? (data.sentimentStats.positive / data.sentimentStats.total) * 100 : 0}
                    strokeColor={{
                      '0%': '#10b981',
                      '100%': '#34d399',
                    }}
                    size={120}
                    strokeWidth={8}
                  />
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div className="text-center p-6 glass-card hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-red-600 mb-4">
                    {data ? ((data.sentimentStats.negative / data.sentimentStats.total) * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-gray-500 mb-6 font-medium">负面情感占比</div>
                  <Progress
                    type="circle"
                    percent={data ? (data.sentimentStats.negative / data.sentimentStats.total) * 100 : 0}
                    strokeColor={{
                      '0%': '#ef4444',
                      '100%': '#f87171',
                    }}
                    size={120}
                    strokeWidth={8}
                  />
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div className="text-center p-6 glass-card hover:scale-105 transition-all duration-300">
                  <div className="text-4xl font-bold text-blue-600 mb-4">
                    {data ? ((data.sentimentStats.neutral / data.sentimentStats.total) * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-gray-500 mb-6 font-medium">中性情感占比</div>
                  <Progress
                    type="circle"
                    percent={data ? (data.sentimentStats.neutral / data.sentimentStats.total) * 100 : 0}
                    strokeColor={{
                      '0%': '#6366f1',
                      '100%': '#8b5cf6',
                    }}
                    size={120}
                    strokeWidth={8}
                  />
                </div>
              </Col>
            </Row>
          </div>
        </>
      )}
    </div>
  )
}