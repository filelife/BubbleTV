# 快速参考 - 核心类和方法速查

## RedisManager - 数据存储管理

### 任务管理
```python
set_task(task_id, task_data) -> bool
get_task(task_id) -> dict | None
get_all_tasks() -> list
update_task_status(task_id, status, progress=None, save_path=None, error_message=None, clear_error=False)
task_exists(task_id) -> bool
delete_task(task_id) -> bool
```

### Cookie管理
```python
set_cookie(platform, cookie_data) -> bool
get_cookie(platform) -> dict | None
delete_cookie(platform) -> bool
```

### 配置管理
```python
set_storage_path(storage_path) -> bool
get_storage_path() -> str
set_migration_status(status) -> bool
get_migration_status() -> str
```

---

## VideoParser - URL解析

```python
detect_platform(url) -> str | None
    # 返回：bilibili/douyin/toutiao/None

detect_video_type(url, platform) -> str
    # 返回：短视频/长视频/番剧

parse_video_info(url) -> dict
    # 返回：{title, platform, video_type, video_url, audio_url}
```

---

## VideoDownloader - 视频下载

```python
download_video(task_id, url, output_path, cookie_data=None) -> (bool, str)
    # 主下载方法
    # 返回：(是否成功, 消息)

_download_douyin_with_ytdlp(url, task_id, output_path, cookie_data=None) -> (bool, str)
    # 使用yt-dlp下载抖音

_download_douyin_manual(url, task_id, output_path) -> (bool, str)
    # 手动下载抖音（备用）

_download_other_platform(url, task_id, output_path, cookie_data=None) -> (bool, str)
    # 下载其他平台

_get_safe_filename(title) -> str
    # 生成安全文件名
```

---

## VideoScraper - 视频爬取

```python
scrape_video(url, cookie_data=None) -> dict
    # 主爬取方法
    # 返回：{title, video_url, audio_url, platform}

_detect_platform(url) -> str | None
    # 识别平台

_scrape_bilibili(url, cookie_data=None) -> dict
    # 爬取B站

_scrape_douyin(url, cookie_data=None) -> dict
    # 爬取抖音

_scrape_toutiao(url, cookie_data=None) -> dict
    # 爬取头条
```

---

## VideoTranscoder - 视频转码

```python
transcode_video(input_file, output_file, task_id=None) -> (bool, str)
    # 转码单个视频
    # 返回：(是否成功, 消息)

batch_transcode(input_files, output_dir, task_id=None) -> dict
    # 批量转码
    # 返回：{total, success, failed, failed_files}

check_ffmpeg_installed() -> bool
    # 检查FFmpeg是否安装
```

---

## PlatformAuth - 平台认证

```python
save_auth(platform, auth_data) -> bool
    # 保存认证信息

get_auth(platform) -> dict | None
    # 获取认证信息

delete_auth(platform) -> bool
    # 删除认证信息

get_all_auth() -> list
    # 获取所有认证信息
```

---

## StorageManager - 存储管理

```python
get_storage_path() -> str
    # 获取存储路径

set_storage_path(new_path) -> bool
    # 设置存储路径

migrate_storage(old_path, new_path) -> dict
    # 迁移存储路径
    # 返回：{total, success, failed, progress}
```

---

## Flask API端点

### 任务管理
```
GET  /api/tasks                    # 获取所有任务
POST /api/tasks                    # 创建新任务
POST /api/tasks/<id>/retry         # 重试任务
POST /api/tasks/<id>/open          # 打开文件
DELETE /api/tasks/<id>             # 删除任务
```

### 平台认证
```
POST   /api/auth/platform          # 保存认证
GET    /api/auth/platform/<platform> # 获取认证
DELETE /api/auth/platform/<platform> # 删除认证
```

---

## 任务状态

- `pending` - 等待中
- `downloading` - 下载中
- `transcoding` - 转码中
- `completed` - 已完成
- `failed` - 失败

---

## 平台名称

- `bilibili` - B站
- `douyin` - 抖音
- `toutiao` - 头条

---

## 视频类型

- `短视频` - 短视频
- `长视频` - 长视频
- `番剧` - 番剧

---

## 任务数据结构

```python
{
    'id': str,              # 任务ID
    'url': str,             # 视频URL
    'title': str,           # 视频标题
    'platform': str,        # 平台名称
    'video_type': str,      # 视频类型
    'status': str,          # 状态
    'progress': str,        # 进度（0-100）
    'save_path': str,       # 保存路径
    'error_message': str,   # 错误信息
    'created_at': str,      # 创建时间
    'updated_at': str       # 更新时间
}
```

---

## 错误信息格式

### 下载失败
```
下载失败: {错误详情}

解析的视频URL: {video_url}
```

### 转码失败
```
转码失败: {错误详情}

解析的视频URL: {video_url}
```

---

## 常见操作

### 创建任务
```python
task_id = str(uuid.uuid4())
task_data = {
    'id': task_id,
    'url': url,
    'title': title,
    'platform': platform,
    'video_type': video_type,
    'status': 'pending',
    'created_at': datetime.now().isoformat()
}
redis_manager.set_task(task_id, task_data)
```

### 更新任务状态
```python
redis_manager.update_task_status(
    task_id,
    'downloading',
    progress=50,
    error_message='错误信息'
)
```

### 清除错误信息
```python
redis_manager.update_task_status(
    task_id,
    'pending',
    clear_error=True
)
```

### 获取任务
```python
task = redis_manager.get_task(task_id)
if task:
    print(task['status'])
```

### 删除任务
```python
redis_manager.delete_task(task_id)
```

---

## 调试命令

### 查看所有任务
```python
tasks = redis_manager.get_all_tasks()
for task in tasks:
    print(f"{task['id']}: {task['status']}")
```

### 查看特定任务
```python
task = redis_manager.get_task(task_id)
print(task)
```

### 测试URL解析
```python
from video_downloader import VideoParser
parser = VideoParser()
platform = parser.detect_platform(url)
info = parser.parse_video_info(url)
```

### 测试视频爬取
```python
from video_scraper import VideoScraper
scraper = VideoScraper()
info = scraper.scrape_video(url)
```

---

## 配置文件 (config.py)

```python
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

FFMPEG_PATH = 'ffmpeg'
OUTPUT_FORMAT = 'mov'

SECRET_KEY = 'your-secret-key-here'

DEFAULT_STORAGE_PATH = './downloads'
```

---

## 文件路径

- `app.py` - Flask应用
- `redis_manager.py` - Redis管理
- `video_downloader.py` - 视频下载器（包含VideoParser）
- `video_scraper.py` - 视频爬虫
- `video_transcoder.py` - 视频转码器
- `platform_auth.py` - 平台认证
- `storage_manager.py` - 存储管理
- `config.py` - 配置
- `static/js/app.js` - 前端JS
- `templates/index.html` - 主页面

---

## 常见问题

### Q: 如何添加新平台支持？
1. 在`VideoParser.platform_patterns`中添加规则
2. 在`VideoScraper`中添加`_scrape_<platform>()`方法
3. 在`VideoDownloader`中添加下载逻辑

### Q: 如何修改错误信息？
1. 找到错误生成的位置（`video_downloader.py`）
2. 修改`error_msg`字符串
3. 确保包含视频URL（如果有）

### Q: 如何修改转码参数？
1. 修改`VideoTranscoder.transcode_video()`中的`cmd`参数
2. 调整FFmpeg参数

### Q: 如何添加新的API端点？
1. 在`app.py`中添加路由
2. 使用`RedisManager`访问数据
3. 返回JSON响应