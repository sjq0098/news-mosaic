import type { AppProps } from 'next/app'
import { ConfigProvider, theme } from 'antd'
import { useState, useEffect } from 'react'
import { AuthProvider } from '../contexts/AuthContext'
import '../styles/globals.css'

// Ant Design 主题配置
const lightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 8,
    wireframe: false,
  },
}

const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 8,
    wireframe: false,
  },
}

export default function App({ Component, pageProps }: AppProps) {
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    // 检查本地存储的主题设置
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      setIsDarkMode(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = !isDarkMode
    setIsDarkMode(newTheme)
    localStorage.setItem('theme', newTheme ? 'dark' : 'light')
    if (newTheme) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  return (
    <ConfigProvider theme={isDarkMode ? darkTheme : lightTheme}>
      <AuthProvider>
        <div className={isDarkMode ? 'dark' : ''}>
          <Component {...pageProps} toggleTheme={toggleTheme} isDarkMode={isDarkMode} />
        </div>
      </AuthProvider>
    </ConfigProvider>
  )
}