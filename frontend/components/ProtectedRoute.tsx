import React, { useEffect } from 'react'
import { useRouter } from 'next/router'
import { Spin, Result, Button } from 'antd'
import { LoadingOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from './AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
  fallback?: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  redirectTo = '/login',
  fallback
}) => {
  const router = useRouter()
  const { isAuthenticated, isLoading, user } = useAuth()

  useEffect(() => {
    // 如果需要认证但用户未登录，重定向到登录页
    if (requireAuth && !isLoading && !isAuthenticated) {
      const currentPath = router.asPath
      const loginUrl = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`
      router.replace(loginUrl)
    }
  }, [requireAuth, isLoading, isAuthenticated, router, redirectTo])

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Spin 
            indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} 
            size="large" 
          />
          <div className="mt-4 text-lg text-gray-600">加载中...</div>
        </div>
      </div>
    )
  }

  // 如果需要认证但用户未登录
  if (requireAuth && !isAuthenticated) {
    // 如果提供了自定义fallback，使用它
    if (fallback) {
      return <>{fallback}</>
    }

    // 默认的未认证页面
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Result
          icon={<LockOutlined className="text-blue-500" />}
          title="需要登录"
          subTitle="请先登录以访问此页面"
          extra={
            <Button 
              type="primary" 
              onClick={() => router.push(redirectTo)}
              className="bg-blue-500 hover:bg-blue-600"
            >
              去登录
            </Button>
          }
        />
      </div>
    )
  }

  // 如果不需要认证或用户已登录，渲染子组件
  return <>{children}</>
}

export default ProtectedRoute

// 高阶组件版本
export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<ProtectedRouteProps, 'children'> = {}
) => {
  const AuthenticatedComponent: React.FC<P> = (props) => {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    )
  }

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name})`
  
  return AuthenticatedComponent
}

// 角色保护组件
interface RoleProtectedProps {
  children: React.ReactNode
  allowedRoles: string[]
  fallback?: React.ReactNode
}

export const RoleProtected: React.FC<RoleProtectedProps> = ({
  children,
  allowedRoles,
  fallback
}) => {
  const { user, isAuthenticated } = useAuth()

  // 如果未登录，不渲染任何内容
  if (!isAuthenticated || !user) {
    return null
  }

  // 检查用户角色
  const hasPermission = allowedRoles.includes(user.role)

  if (!hasPermission) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您没有权限访问此页面"
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回
          </Button>
        }
      />
    )
  }

  return <>{children}</>
}

// 权限检查Hook
export const usePermission = (requiredRoles: string[]) => {
  const { user, isAuthenticated } = useAuth()

  const hasPermission = isAuthenticated && user && requiredRoles.includes(user.role)
  
  return {
    hasPermission,
    user,
    isAuthenticated
  }
}
