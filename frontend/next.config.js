/** @type {import('next').NextConfig} */
const nextConfig = {
  // 基础配置
  reactStrictMode: true,
  swcMinify: true,
  
  // 输出配置
  output: 'standalone',
  
  // 转译模块配置 - 解决Ant Design ES模块问题
  transpilePackages: ['antd', '@ant-design/icons', '@ant-design/colors'],
  
  // 环境变量
  env: {
    CUSTOM_KEY: 'my-value',
  },
  
  // 国际化配置
  i18n: {
    locales: ['zh-CN', 'en-US'],
    defaultLocale: 'zh-CN',
  },
  
  // 图片优化
  images: {
    domains: [
      'localhost',
      '127.0.0.1',
      'example.com',
      // 添加其他允许的图片域名
    ],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  // 重写规则
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'}/:path*`,
      },
    ];
  },
  
  // 头部配置
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  
  // 重定向
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },
  
  // 实验性功能 - 移除appDir，因为使用的是页面路由
  experimental: {
    serverActions: true,
  },
  
  // Webpack 配置
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 自定义 webpack 配置
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    
    // 解决ES模块问题
    config.resolve.extensionAlias = {
      '.js': ['.js', '.ts', '.tsx'],
    };
    
    return config;
  },
  
  // TypeScript 配置
  typescript: {
    ignoreBuildErrors: false,
  },
  
  // ESLint 配置
  eslint: {
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig;