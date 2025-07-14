#!/bin/bash

echo "====================================="
echo "     News Mosaic 启动脚本 (Unix)"
echo "====================================="
echo

echo "[1/4] 激活 conda 环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate news-mosaic

if [ $? -ne 0 ]; then
    echo "错误: 无法激活 conda 环境 'news-mosaic'"
    echo "请先运行: conda create -n news-mosaic python=3.10 -y"
    exit 1
fi

echo "[2/4] 检查环境配置..."
if [ ! -f "backend/.env" ]; then
    echo "错误: 未找到 backend/.env 文件"
    echo "请复制 backend/.env.example 到 backend/.env 并配置相应参数"
    exit 1
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "警告: 未找到 frontend/.env.local 文件"
    echo "将使用默认配置"
fi

echo "[3/4] 启动后端服务..."
cd backend
gnome-terminal --title="News Mosaic Backend" -- bash -c "conda activate news-mosaic && uvicorn main:app --reload --host 0.0.0.0 --port 8000; exec bash" &

echo "[4/4] 启动前端服务..."
cd ../frontend
gnome-terminal --title="News Mosaic Frontend" -- bash -c "npm run dev; exec bash" &

echo
echo "====================================="
echo "     服务启动完成！"
echo "====================================="
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000" 
echo "API 文档: http://localhost:8000/docs"
echo
echo "按 Ctrl+C 退出"

# 保持脚本运行
wait 