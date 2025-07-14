@echo off
chcp 65001 > nul
echo =====================================
echo     News Mosaic 启动脚本 (Windows)
echo =====================================
echo.

echo [1/4] 激活 conda 环境...
call conda activate news-mosaic
if %errorlevel% neq 0 (
    echo 错误: 无法激活 conda 环境 'news-mosaic'
    echo 请先运行: conda create -n news-mosaic python=3.10 -y
    pause
    exit /b 1
)

echo [2/4] 检查环境配置...
if not exist "backend\.env" (
    echo 错误: 未找到 backend\.env 文件
    echo 请复制 backend\.env.example 到 backend\.env 并配置相应参数
    pause
    exit /b 1
)

if not exist "frontend\.env.local" (
    echo 警告: 未找到 frontend\.env.local 文件
    echo 将使用默认配置
)

echo [3/4] 启动后端服务...
cd backend
start "News Mosaic Backend" cmd /k "conda activate news-mosaic && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [4/4] 启动前端服务...
cd ..\frontend
start "News Mosaic Frontend" cmd /k "npm run dev"

echo.
echo =====================================
echo     服务启动完成！
echo =====================================
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:3000
echo API 文档: http://localhost:8000/docs
echo.
echo 按任意键关闭此窗口...
pause 