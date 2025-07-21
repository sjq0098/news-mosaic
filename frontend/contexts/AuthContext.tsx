import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { message } from 'antd'
import { userApi } from '../services/api'

// 用户信息接口
interface User {
  id: string
  username: string
  email?: string
  nickname?: string
  avatar_url?: string
  bio?: string
  role: string
  preferences?: any
}

// 认证上下文接口
interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  register: (userData: RegisterData) => Promise<boolean>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
  refreshUserProfile: () => Promise<void>
}

// 注册数据接口
interface RegisterData {
  username: string
  email: string
  password: string
  nickname?: string
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// 认证提供者组件
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 计算认证状态
  const isAuthenticated = !!user

  // 初始化认证状态
  useEffect(() => {
    initializeAuth()
  }, [])

  // 初始化认证
  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setIsLoading(false)
        return
      }

      // 验证token并获取用户信息
      await refreshUserProfile()
    } catch (error) {
      console.error('初始化认证失败:', error)
      // 清除无效token
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    } finally {
      setIsLoading(false)
    }
  }

  // 登录
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await userApi.login({ username, password })
      
      if (response.data.status === 'success') {
        // 保存token
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        
        // 设置用户信息
        const userData: User = {
          id: response.data.user_id,
          username: response.data.username,
          role: 'user' // 默认角色
        }
        
        setUser(userData)
        localStorage.setItem('user', JSON.stringify(userData))
        
        // 获取完整用户档案
        await refreshUserProfile()
        
        message.success('登录成功！')
        return true
      } else {
        message.error(response.data.message || '登录失败')
        return false
      }
    } catch (error: any) {
      console.error('登录失败:', error)
      message.error(error.response?.data?.detail || '登录失败，请检查网络连接')
      return false
    }
  }

  // 注册
  const register = async (userData: RegisterData): Promise<boolean> => {
    try {
      const response = await userApi.register(userData)
      
      if (response.data.status === 'success') {
        message.success('注册成功！请登录')
        return true
      } else {
        message.error(response.data.message || '注册失败')
        return false
      }
    } catch (error: any) {
      console.error('注册失败:', error)
      message.error(error.response?.data?.detail || '注册失败，请检查网络连接')
      return false
    }
  }

  // 登出
  const logout = () => {
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    message.success('已退出登录')
  }

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData }
      setUser(updatedUser)
      localStorage.setItem('user', JSON.stringify(updatedUser))
    }
  }

  // 刷新用户档案
  const refreshUserProfile = async () => {
    try {
      const response = await userApi.getUserProfile()
      const profileData = response.data
      
      const userData: User = {
        id: profileData.id,
        username: profileData.username,
        email: profileData.email,
        nickname: profileData.nickname,
        avatar_url: profileData.avatar_url,
        bio: profileData.bio,
        role: profileData.role || 'user',
        preferences: profileData.preferences
      }
      
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error: any) {
      console.error('获取用户档案失败:', error)
      
      // 如果是401错误，说明token已过期
      if (error.response?.status === 401) {
        // 尝试刷新token
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          try {
            const refreshResponse = await userApi.refreshToken(refreshToken)
            localStorage.setItem('token', refreshResponse.data.access_token)
            // 重新获取用户档案
            await refreshUserProfile()
            return
          } catch (refreshError) {
            console.error('刷新token失败:', refreshError)
          }
        }
        
        // 刷新失败，清除认证信息
        logout()
      }
      
      throw error
    }
  }

  // 提供认证上下文值
  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    updateUser,
    refreshUserProfile
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// 认证状态Hook
export const useAuthStatus = () => {
  const { isAuthenticated, isLoading, user } = useAuth()
  return { isAuthenticated, isLoading, user }
}

// 用户信息Hook
export const useUser = () => {
  const { user, updateUser, refreshUserProfile } = useAuth()
  return { user, updateUser, refreshUserProfile }
}

// 认证操作Hook
export const useAuthActions = () => {
  const { login, register, logout } = useAuth()
  return { login, register, logout }
}
