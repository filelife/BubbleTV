#!/bin/bash

echo "正在启动泡泡看视频..."

# 检查Redis是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis未运行，正在启动Redis..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis
    else
        echo "请手动启动Redis"
        exit 1
    fi
    
    sleep 2
fi

# 检查FFmpeg是否安装
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg未安装，请先安装FFmpeg"
    echo "安装方法："
    echo "macOS: brew install ffmpeg"
    echo "Ubuntu/Debian: sudo apt-get install ffmpeg"
    exit 1
fi

# 安装Python依赖
echo "正在安装Python依赖..."
pip3 install -r requirements.txt

# 创建必要的目录
mkdir -p logs
mkdir -p static/js
mkdir -p templates

# 启动Flask应用
echo "启动Flask应用...with port 5001"
python3 app.py