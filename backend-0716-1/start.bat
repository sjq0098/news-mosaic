@echo off
REM 启动 News Mosaic 用户认证服务

echo 启动 News Mosaic 用户认证服务...

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo 已激活虚拟环境
)

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 启动服务
echo 启动用户认证服务...
python main.py

pause
