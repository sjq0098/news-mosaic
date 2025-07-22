import React from 'react'
import { Card, Space } from 'antd'
import MarkdownRenderer from '../components/MarkdownRenderer'

const TestMarkdownPage: React.FC = () => {
  const sampleMarkdown = `# 新闻分析报告

## 主要事件概述

这是一个**重要的新闻事件**，涉及多个方面：

### 关键要点

1. **经济影响**：市场反应积极
2. **社会影响**：公众关注度高
3. **政策影响**：可能引发新的政策调整

### 详细分析

> 根据最新数据显示，这一事件对整个行业产生了深远影响。

#### 数据统计

| 指标 | 数值 | 变化 |
|------|------|------|
| 市场份额 | 25% | +5% |
| 用户增长 | 1000万 | +15% |
| 收入增长 | $50M | +20% |

#### 技术细节

以下是相关的代码示例：

\`\`\`javascript
// 数据处理函数
function processNewsData(data) {
  return data.map(item => ({
    title: item.title,
    summary: item.summary,
    sentiment: analyzeSentiment(item.content)
  }));
}
\`\`\`

#### 相关链接

- [官方公告](https://example.com)
- [详细报告](https://example.com/report)
- [数据分析](https://example.com/analysis)

---

## 结论

通过以上分析，我们可以看出：

- ~~旧的预测~~已经不再适用
- *新的趋势*正在形成
- **重要决策**需要及时做出

\`inline code example\` 也能正常显示。

### 下一步行动

1. 继续监控市场动态
2. 调整投资策略
3. 加强风险控制

> **注意**：以上分析仅供参考，投资有风险，决策需谨慎。`

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card title="Markdown 渲染测试">
          <p>这个页面用于测试 Markdown 渲染器的功能。</p>
        </Card>
        
        <Card title="原始 Markdown 文本">
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '12px'
          }}>
            {sampleMarkdown}
          </pre>
        </Card>
        
        <Card title="渲染后的效果">
          <MarkdownRenderer content={sampleMarkdown} />
        </Card>
      </Space>
    </div>
  )
}

export default TestMarkdownPage
