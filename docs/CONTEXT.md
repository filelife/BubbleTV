# 项目上下文管理文档

## 项目概述
自动下载视频应用 - 一个支持多平台（B站、抖音、头条）视频下载、转码和管理的Web应用。

## ⚠️ 重要：测试和生产环境隔离

**数据库隔离**：
- **生产环境**: Redis DB=0（用于Web应用和用户数据）
- **测试环境**: Redis DB=1（仅用于单元测试和集成测试）

**使用规则**：
- ✅ 所有测试脚本必须使用 `RedisManager(use_test_db=True)`
- ✅ Web应用使用 `RedisManager()`（默认生产环境）
- ❌ 测试脚本不得访问生产数据库（DB=0）
- ❌ 不得直接清理生产环境的任务

**测试脚本模板**：
```python
from redis_manager import RedisManager

# ✅ 正确：使用测试数据库
test_redis = RedisManager(use_test_db=True)

# ❌ 错误：使用生产数据库
prod_redis = RedisManager()
```

**清理测试任务**：
```bash
# 仅清理测试数据库，不影响生产环境
python3 cleanup_tasks.py
```

---

## 技术栈
- **后端**: Flask + Redis
- **前端**: HTML + JavaScript + Bootstrap
- **视频处理**: FFmpeg
- **视频下载**: yt-dlp + 自定义爬虫
- **存储**: 本地文件系统

---

## 核心组件架构

### 1. Flask应用 (app.py)
**职责**: Web服务器和API端点

**核心路由**:
- `GET /` - 返回主页面
- `GET /api/tasks` - 获取所有任务
- `POST /api/tasks` - 创建新任务
- `POST /api/tasks/<task_id>/retry` - 重试失败的任务
- `POST /api/tasks/<task_id>/open` - 打开下载的文件
- `DELETE /api/tasks/<task_id>` - 删除任务
- `POST /api/tasks/<task_id>/pause` - 暂停任务
- `POST /api/tasks/<task_id>/cancel` - 取消任务
- `GET /api/tasks/<task_id>/logs` - 获取任务日志
- `POST /api/auth/platform` - 平台认证
- `GET /api/auth/platform/<platform>` - 获取平台认证状态
- `DELETE /api/auth/platform/<platform>` - 删除平台认证

**全局实例**:
```python
redis_manager = RedisManager()  # 生产环境
video_parser = VideoParser()
video_downloader = VideoDownloader(redis_manager)
platform_auth = PlatformAuth(redis_manager)
video_transcoder = VideoTranscoder(redis_manager)
storage_manager = StorageManager(redis_manager)
```

---

### 2. RedisManager (redis_manager.py)
**职责**: 管理Redis数据存储，提供统一的数据访问接口

**初始化**:
```python
def __init__(self, use_test_db=False):
    db = Config.TEST_REDIS_DB if use_test_db else Config.REDIS_DB
    self.redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=db,  # 根据参数选择数据库
        password=Config.REDIS_PASSWORD,
        decode_responses=True
    )
```

**数据结构**:
- `task:{task_id}` - 任务数据（Hash）
- `user:{user_id}` - 用户数据（Hash）
- `video:{video_id}` - 视频数据（Hash）
- `config:{config_key}` - 配置数据（String）
- `task_log:{task_id}` - 任务日志（List）

**核心方法**:
```python
# 任务管理
set_task(task_id, task_data) -> bool
get_task(task_id) -> dict | None
get_all_tasks() -> list
update_task_status(task_id, status, progress=None, save_path=None, error_message=None, clear_error=False)
task_exists(task_id) -> bool

# 用户管理
set_user(user_id, user_data) -> bool
get_user(user_id) -> dict

# 配置管理
set_storage_path(storage_path) -> bool
get_storage_path() -> str
set_migration_status(status) -> bool
get_migration_status() -> str

# Cookie管理
set_cookie(platform, cookie_data) -> bool
get_cookie(platform) -> dict | None
delete_cookie(platform) -> bool

# 任务日志管理（新增）
add_task_log(task_id, message) -> bool
get_task_logs(task_id) -> list
clear_task_logs(task_id) -> bool
```

**任务数据结构**:
```python
{
    'id': str,              # 任务ID
    'url': str,             # 视频URL
    'title': str,           # 视频标题
    'platform': str,        # 平台名称
    'video_type': str,      # 视频类型（短视频/长视频/番剧）
    'status': str,          # 状态：pending/downloading/transcoding/completed/failed/cancelled
    'progress': str,        # 进度（0-100）
    'save_path': str,       # 保存路径
    'error_message': str,   # 错误信息
    'created_at': str,      # 创建时间
    'updated_at': str       # 更新时间
}
```

**任务状态定义**:
- `pending`: 等待中
- `downloading`: 下载中
- `transcoding`: 转码中
- `completed`: 已完成
- `failed`: 下载失败
- `cancelled`: 已取消

---

### 3. VideoParser (video_downloader.py)
**职责**: 解析视频URL，识别平台和视频类型

**核心方法**:
```python
detect_platform(url) -> str | None
    # 识别平台：bilibili/douyin/toutiao
detect_video_type(url, platform) -> str
    # 识别视频类型：短视频/长视频/番剧
parse_video_info(url) -> dict
    # 解析视频信息
    # 返回：{title, platform, video_type, video_url, audio_url}
```

**平台识别规则**:
- B站: `b23.tv/*`, `bilibili.com/video/*`, `bilibili.com/bangumi/play/*`
- 抖音: `v.douyin.com/*`, `douyin.com/video/*`
- 头条: `m.toutiao.com/is/*`, `toutiao.com/video/*`

---

### 4. VideoDownloader (video_downloader.py)
**职责**: 下载视频，管理下载流程

**初始化**:
```python
def __init__(self, redis_manager):
    self.redis = redis_manager
    self.parser = VideoParser()
    self.scraper = VideoScraper()
    self.transcoder = VideoTranscoder(redis_manager)
```

**核心方法**:
```python
download_video(task_id, url, output_path, cookie_data=None) -> (bool, str)
    # 主下载流程
    # 返回：(是否成功, 消息)

_download_douyin_with_ytdlp(url, task_id, output_path, cookie_data=None) -> (bool, str)
    # 使用yt-dlp下载抖音视频

_download_douyin_manual(url, task_id, output_path) -> (bool, str)
    # 手动下载抖音视频（备用方案）

_download_other_platform(url, task_id, output_path, cookie_data=None) -> (bool, str)
    # 下载其他平台视频

_get_safe_filename(title) -> str
    # 生成安全的文件名

_ytdlp_progress_hook(d, task_id)
    # yt-dlp进度回调

_log(task_id, message) -> None
    # 记录任务日志（新增）
```

**下载流程**:
1. 阶段1: 准备下载参数
2. 阶段2: 配置下载工具
3. 阶段3: 执行下载
4. 阶段4: 检查下载结果
5. 阶段5: 转码为mov格式

**错误处理**:
- 所有错误信息都包含解析出来的视频URL
- 支持重试失败的任务
- 错误信息存储在Redis中
- **下载超时优化**：大视频下载超时从30秒延长到600秒（10分钟）

---

### 5. VideoScraper (video_scraper.py)
**职责**: 爬取视频信息，获取视频下载链接

**核心方法**:
```python
scrape_video(url, cookie_data=None) -> dict
    # 主爬取方法
    # 返回：{title, video_url, audio_url, platform}

_detect_platform(url) -> str | None
    # 识别平台

_scrape_bilibili(url, cookie_data=None) -> dict
    # 爬取B站视频

_scrape_douyin(url, cookie_data=None) -> dict
    # 爬取抖音视频

_scrape_toutiao(url, cookie_data=None) -> dict
    # 爬取头条视频
```

**支持的爬取方法**:
- B站: API爬取 + HTML解析
- 抖音: yt-dlp + 手动爬取 + 第三方API
- 头条: HTML解析 + API爬取

---

### 6. VideoTranscoder (video_transcoder.py)
**职责**: 视频转码，监控转码进度

**初始化**:
```python
def __init__(self, redis_manager):
    self.redis = redis_manager
    self.ffmpeg_path = Config.FFMPEG_PATH
    self.output_format = Config.OUTPUT_FORMAT  # 默认mov
```

**核心方法**:
```python
transcode_video(input_file, output_file, task_id=None) -> (bool, str)
    # 转码单个视频
    # 返回：(是否成功, 消息)

batch_transcode(input_files, output_dir, task_id=None) -> dict
    # 批量转码
    # 返回：{total, success, failed, failed_files}

_monitor_progress(process, task_id)
    # 监控FFmpeg转码进度
    # 解析FFmpeg输出：time=HH:MM:SS

check_ffmpeg_installed() -> bool
    # 检查FFmpeg是否安装

_get_video_duration(input_file) -> float
    # 获取视频时长（秒）
    # 使用FFmpeg解析视频信息，提取Duration字段
    # 转换为总秒数：hours * 3600 + minutes * 60 + seconds

_log(task_id, message) -> None
    # 记录任务日志（新增）
```

**转码参数**:
```python
{
    'codec': 'libx264',
    'preset': 'medium',
    'crf': '23',
    'audio_codec': 'aac',
    'audio_bitrate': '128k',
    'format': 'mov'
}
```

**进度监控**:
- 解析FFmpeg输出中的`time=HH:MM:SS`
- 转换为总秒数计算进度
- 防止除零错误
- 限制进度在0-100之间
- **使用实际视频时长**：避免固定时长导致进度不准确
- **独立线程监控**：使用独立线程监控FFmpeg输出，避免进程通信死锁
- **30分钟超时保护**：转码超时自动终止进程

---

### 7. PlatformAuth (platform_auth.py)
**职责**: 管理平台认证信息（Cookie）

**核心方法**:
```python
save_auth(platform, auth_data) -> bool
    # 保存平台认证信息

get_auth(platform) -> dict | None
    # 获取平台认证信息

delete_auth(platform) -> bool
    # 删除平台认证信息

get_all_auth() -> list
    # 获取所有平台认证信息
```

**认证数据结构**:
```python
{
    'platform': str,      # 平台名称
    'cookie': str,        # Cookie字符串
    'created_at': str     # 创建时间
}
```

---

### 8. StorageManager (storage_manager.py)
**职责**: 管理存储路径，处理存储迁移

**核心方法**:
```python
get_storage_path() -> str
    # 获取当前存储路径

set_storage_path(new_path) -> bool
    # 设置新的存储路径

migrate_storage(old_path, new_path) -> dict
    # 迁移存储路径
    # 返回：{total, success, failed, progress}

_get_migration_progress() -> int
    # 获取迁移进度
```

---

## 数据流

### 任务创建流程
```
用户提交URL
    ↓
VideoParser.detect_platform(url)
    ↓
VideoParser.parse_video_info(url)
    ↓
创建任务数据
    ↓
RedisManager.set_task(task_id, task_data)
    ↓
添加到下载队列
    ↓
VideoDownloader.download_video()
```

### 下载流程
```
VideoDownloader.download_video()
    ↓
识别平台
    ↓
获取Cookie（如果有）
    ↓
VideoScraper.scrape_video() 获取视频URL
    ↓
下载视频文件
    ↓
检查文件大小
    ↓
VideoTranscoder.transcode_video() 转码
    ↓
更新任务状态为completed
```

### 错误处理流程
```
下载失败
    ↓
生成错误信息（包含视频URL）
    ↓
RedisManager.update_task_status(status='failed', error_message=...)
    ↓
用户查看错误信息
    ↓
点击"重试"按钮
    ↓
RedisManager.update_task_status(status='pending', clear_error=True)
    ↓
重新加入下载队列
```

### 任务取消流程（新增）
```
用户点击"取消"按钮
    ↓
POST /api/tasks/<task_id>/cancel
    ↓
RedisManager.update_task_status(status='cancelled')
    ↓
下载/转码进程终止
    ↓
任务状态更新为cancelled
    ↓
UI显示"重试"和"删除"按钮
```

---

## 关键配置

### Config (config.py)
```python
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
TEST_REDIS_DB = 1  # 测试环境数据库

FFMPEG_PATH = 'ffmpeg'
OUTPUT_FORMAT = 'mov'
SECRET_KEY = 'your-secret-key-here'
DEFAULT_STORAGE_PATH = './downloads'
```

---

## 常见任务模式

### 1. 添加新平台支持
1. 在`VideoParser.platform_patterns`中添加平台识别规则
2. 在`VideoScraper`中添加`_scrape_<platform>()`方法
3. 在`VideoDownloader`中添加下载逻辑

### 2. 修改错误信息
1. 找到错误生成的位置（`video_downloader.py`）
2. 修改`error_msg`字符串
3. 确保包含视频URL（如果有）
4. 使用`RedisManager.update_task_status()`更新

### 3. 添加新的API端点
1. 在`app.py`中添加路由
2. 使用`RedisManager`访问数据
3. 返回JSON响应

### 4. 修改转码参数
1. 修改`VideoTranscoder.transcode_video()`中的`cmd`参数
2. 调整FFmpeg参数

### 5. 添加任务日志功能（新增）
1. 在`RedisManager`中添加日志存储方法
2. 在`VideoDownloader`和`VideoTranscoder`中添加`_log()`方法
3. 在`app.py`中添加`GET /api/tasks/<task_id>/logs`API端点
4. 在前端添加"日志"按钮和日志查看功能

---

## 调试技巧

### 1. 查看任务状态
```python
redis_manager.get_task(task_id)
```

### 2. 查看所有任务
```python
redis_manager.get_all_tasks()
```

### 3. 查看任务日志（新增）
```python
redis_manager.get_task_logs(task_id)
```

### 4. 查看平台认证
```python
platform_auth.get_auth('bilibili')
```

### 5. 测试视频解析
```python
video_parser.parse_video_info(url)
```

### 6. 测试视频爬取
```python
video_scraper.scrape_video(url)
```

### 7. 运行单元测试
```bash
# 使用测试数据库，不影响生产环境
python3 test_bilibili_download.py
```

---

## 注意事项

1. **错误信息格式**: 所有错误信息都应包含视频URL（如果有）
2. **任务状态更新**: 使用`RedisManager.update_task_status()`统一更新
3. **进度监控**: 转码进度需要防止除零错误
4. **文件路径**: 使用绝对路径，避免相对路径问题
5. **Cookie管理**: 敏感信息，注意安全
6. **并发下载**: 使用线程池，避免阻塞主线程
7. **错误重试**: 失败的任务可以重试，需要清除旧的错误信息
8. **任务日志**: 记录任务执行过程中的关键信息，便于问题诊断
9. **转码进度**: 使用实际视频时长计算进度，避免固定时长导致进度不准确
10. **下载超时**: 大视频下载需要更长的超时时间（600秒）
11. **进程通信**: 避免同时使用`process.communicate()`和`process.wait()`
12. **测试隔离**: 测试脚本必须使用测试数据库，不得访问生产环境

---

## 文件结构

```
AutoDownloadVideoApp/
├── app.py                    # Flask应用主文件
├── redis_manager.py          # Redis数据管理
├── video_downloader.py       # 视频下载器（包含VideoParser和VideoDownloader）
├── video_scraper.py         # 视频爬虫
├── video_transcoder.py      # 视频转码器
├── platform_auth.py         # 平台认证管理
├── storage_manager.py       # 存储管理
├── config.py               # 配置文件
├── static/
│   └── js/
│       └── app.js         # 前端JavaScript
├── templates/
│   └── index.html        # 主页面
├── downloads/            # 默认存储路径
├── test_bilibili_download.py  # B站下载单元测试
└── cleanup_tasks.py       # 清理测试任务脚本
```

---

## 版本历史

### v1.0
- 基础功能：B站、抖音、头条视频下载
- 视频转码为mov格式
- 任务管理和进度显示
- 平台认证支持

### v1.1
- 添加错误信息复制功能
- 修复重试任务时错误信息未清除的问题
- 修复转码时的除零错误
- 错误信息中包含视频URL

### v1.2
- 添加任务日志系统
- 修复转码进度不准确问题
- 使用实际视频时长计算进度
- 添加转码超时保护（30分钟）
- 优化下载超时设置（600秒）
- 添加任务取消功能
- 修复进程通信死锁问题
- 添加测试数据库隔离
- 添加单元测试脚本

---

## 待优化项

1. 支持更多视频平台
2. 添加视频预览功能
3. 优化下载速度
4. 添加批量下载功能
5. 支持自定义转码参数
6. 添加下载历史记录
7. 支持视频质量选择
8. 优化任务日志显示（支持日志导出）
9. 添加任务暂停功能
10. 支持断点续传
