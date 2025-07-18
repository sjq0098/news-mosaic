#!/bin/bash
# 启动 News Mosaic 用户认证服务

echo "启动 News Mosaic 用户认证服务..."

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "已激活虚拟环境"
fi

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 启动服务
echo "启动用户认证服务..."
python main.py
