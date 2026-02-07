# 泡泡看视频

自动视频下载应用，支持抖音、今日头条、Bilibili三个站点的视频下载。

## 功能特性

- 自动识别视频平台和类型
- 支持平台账号登录和Cookie管理
- 视频下载和自动转码为MOV格式
- 存储目录管理和迁移
- 树状结构目录展示
- 实时搜索功能
- 拖拽文件管理

## 技术栈

- 后端：Python Flask + Redis
- 前端：HTML + JavaScript + Bootstrap
- 视频处理：FFmpeg
- 下载工具：yt-dlp

## 安装

### 依赖安装

```bash
pip install -r requirements.txt
```

### Redis安装

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# 下载并安装Redis for Windows
```

### FFmpeg安装

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# 下载并安装FFmpeg
```

## 运行

```bash
python app.py
```

访问 http://localhost:5000

## 配置

编辑 `config.py` 文件配置应用参数：

```python
# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 存储配置
DEFAULT_STORAGE_PATH = '/Users/username/Downloads/Videos'

# 下载配置
MAX_DOWNLOAD_THREADS = 3
DOWNLOAD_TIMEOUT = 300

# 转码配置
FFMPEG_PATH = '/usr/local/bin/ffmpeg'
OUTPUT_FORMAT = 'mov'
```

## 使用说明

1. 首次使用时选择存储目录
2. 在登录页面登录各平台账号
3. 输入视频链接开始下载
4. 在已下载资源中管理文件
5. 可随时更换存储目录

## 许可证

保留所有权利