import requests
import re
import time
import os
import http.cookiejar
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import yt_dlp
from .video_scraper import VideoScraper
from .video_transcoder import VideoTranscoder

class VideoParser:
    def __init__(self):
        self.platform_patterns = {
            'bilibili': [
                r'b23\.tv/([a-zA-Z0-9]+)',
                r'bilibili\.com/video/([a-zA-Z0-9]+)',
                r'bilibili\.com/video/BV([a-zA-Z0-9]+)',
                r'bilibili\.com/bangumi/play/ep([0-9]+)'
            ],
            'douyin': [
                r'v\.douyin\.com/([a-zA-Z0-9]+)',
                r'douyin\.com/video/([0-9]+)'
            ],
            'toutiao': [
                r'm\.toutiao\.com/is/([a-zA-Z0-9]+)',
                r'toutiao\.com/video/([0-9]+)'
            ]
        }
        self.scraper = VideoScraper()
    
    def detect_platform(self, url):
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url):
                    return platform
        return None
    
    def detect_video_type(self, url, platform):
        if platform == 'bilibili':
            return self._detect_bilibili_type(url)
        elif platform == 'douyin':
            return self._detect_douyin_type(url)
        elif platform == 'toutiao':
            return self._detect_toutiao_type(url)
        return '短视频'
    
    def _detect_bilibili_type(self, url):
        if re.search(r'bilibili\.com/video/BV', url):
            return '短视频'
        elif re.search(r'bilibili\.com/medialist', url):
            return '影视剧'
        elif re.search(r'bilibili\.com/bangumi', url):
            return '番剧'
        return '短视频'
    
    def _detect_douyin_type(self, url):
        return '短视频'
    
    def _detect_toutiao_type(self, url):
        return '短视频'
    
    def parse_video_info(self, url):
        url = self._clean_url(url)
        
        if not self._is_valid_url(url):
            raise ValueError('无效的视频链接格式')
        
        platform = self.detect_platform(url)
        if not platform:
            raise ValueError('不支持的视频平台')
        
        try:
            return self.scraper.scrape_video(url)
        except Exception as e:
            raise Exception(f'解析视频信息失败: {str(e)}')
    
    def _clean_url(self, url):
        url = url.strip()
        url_pattern = r'(https?://[^\s\]\)`\'"]+)'
        match = re.search(url_pattern, url)
        if match:
            return match.group(1)
        return url
    
    def _is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _parse_bilibili(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title')
        if title:
            title = title.string.strip()
        else:
            title = '未知标题'
        
        return {
            'title': title,
            'platform': 'bilibili',
            'url': url,
            'video_type': self.detect_video_type(url, 'bilibili')
        }
    
    def _parse_douyin(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title')
        if title:
            title = title.string.strip()
        else:
            title = '未知标题'
        
        return {
            'title': title,
            'platform': 'douyin',
            'url': url,
            'video_type': self.detect_video_type(url, 'douyin')
        }
    
    def _parse_toutiao(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title')
        if title:
            title = title.string.strip()
        else:
            title = '未知标题'
        
        return {
            'title': title,
            'platform': 'toutiao',
            'url': url,
            'video_type': self.detect_video_type(url, 'toutiao')
        }


class VideoDownloader:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.parser = VideoParser()
        self.scraper = VideoScraper()
        self.transcoder = VideoTranscoder(redis_manager)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _log(self, task_id, message):
        """记录任务日志"""
        if task_id:
            self.redis.add_task_log(task_id, message)
            print(f"[{task_id[:8]}] {message}")
        else:
            print(f"[LOG] {message}")
    
    def _format_speed(self, speed_bytes):
        if speed_bytes < 1024:
            return f'{speed_bytes:.2f} B/s'
        elif speed_bytes < 1024 * 1024:
            return f'{speed_bytes / 1024:.2f} KB/s'
        elif speed_bytes < 1024 * 1024 * 1024:
            return f'{speed_bytes / (1024 * 1024):.2f} MB/s'
        else:
            return f'{speed_bytes / (1024 * 1024 * 1024):.2f} GB/s'
    
    def _download_douyin_with_ytdlp(self, url, task_id, output_path, cookie_data=None):
        try:
            print("=" * 60)
            print(f"📥 开始yt-dlp下载抖音视频")
            print("=" * 60)
            
            # 阶段1: 准备下载
            print(f"📁 阶段1: 准备下载参数")
            try:
                safe_filename = self._get_safe_filename('douyin_video')
                temp_file = os.path.join(os.path.dirname(output_path), f"{safe_filename}.mp4")
                print(f"✅ 临时文件路径: {temp_file}")
            except Exception as e:
                print(f"❌ 阶段1失败: 准备参数错误")
                print(f"   错误详情: {str(e)}")
                raise Exception(f'准备下载参数失败: {str(e)}')
            
            # 阶段2: 配置yt-dlp
            print(f"⚙️  阶段2: 配置yt-dlp参数")
            try:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': temp_file,
                    'quiet': False,
                    'no_warnings': False,
                    'progress_hooks': [lambda d: self._ytdlp_progress_hook(d, task_id)],
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                    'nocheckcertificate': True,
                    'ignoreerrors': False,
                    'extract_flat': False,
                }
                
                # 如果有Cookie，添加到yt-dlp配置
                if cookie_data and 'cookie' in cookie_data:
                    print(f"✅ 使用Cookie进行下载")
                    # 将Cookie字符串转换为Netscape格式并保存到临时文件
                    import tempfile
                    cookie_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                    
                    # 写入Netscape格式头部
                    cookie_file.write("# Netscape HTTP Cookie File\n")
                    cookie_file.write("# This is a generated file! Do not edit.\n\n")
                    
                    # 解析Cookie字符串并转换为Netscape格式
                    cookies = cookie_data['cookie'].split(';')
                    for cookie in cookies:
                        cookie = cookie.strip()
                        if '=' in cookie:
                            name, value = cookie.split('=', 1)
                            # Netscape格式: domain \t flag \t path \t secure \t expiration \t name \t value
                            # domain设置为.douyin.com，flag为TRUE表示子域名也有效
                            cookie_file.write(f".douyin.com\tTRUE\t/\tFALSE\t9999999999\t{name.strip()}\t{value.strip()}\n")
                    
                    cookie_file.close()
                    ydl_opts['cookiefile'] = cookie_file.name
                    print(f"✅ Cookie已保存到Netscape格式文件: {cookie_file.name}")
                else:
                    print(f"⚠️  未提供Cookie，尝试无Cookie下载")
                
                print(f"✅ yt-dlp配置完成")
            except Exception as e:
                print(f"❌ 阶段2失败: 配置yt-dlp错误")
                print(f"   错误详情: {str(e)}")
                raise Exception(f'配置yt-dlp失败: {str(e)}')
            
            # 阶段3: 执行下载
            print(f"📥 阶段3: 执行yt-dlp下载")
            try:
                import yt_dlp
                print(f"✅ yt-dlp导入成功")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    print(f"🚀 开始下载: {url}")
                    try:
                        ydl.download([url])
                        print(f"✅ yt-dlp下载完成")
                    except Exception as download_error:
                        print(f"❌ 阶段3失败: yt-dlp下载错误")
                        print(f"   错误详情: {str(download_error)}")
                        print(f"   错误类型: {type(download_error).__name__}")
                        import traceback
                        traceback.print_exc()
                        raise Exception(f'yt-dlp下载失败: {str(download_error)}')
            except ImportError as ie:
                print(f"❌ 阶段3失败: yt-dlp未安装")
                print(f"   错误详情: {str(ie)}")
                raise Exception(f'yt-dlp未安装，无法下载抖音视频')
            except Exception as e:
                print(f"❌ 阶段3失败: 下载过程错误")
                print(f"   错误详情: {str(e)}")
                print(f"   错误类型: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                raise
            
            # 阶段4: 检查下载结果
            print(f"🔍 阶段4: 检查下载结果")
            try:
                if os.path.exists(temp_file):
                    file_size = os.path.getsize(temp_file)
                    print(f"✅ 文件已创建: {temp_file}")
                    print(f"   文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                    
                    if file_size > 0:
                        print(f"✅ 文件大小正常，准备转码")
                    else:
                        print(f"❌ 文件大小为0，下载失败")
                        # 添加原始URL到错误信息
                        error_msg = f'下载失败: 下载的文件大小为0，可能是网页未正确解析出视频下载地址\n\n原始URL: {url}'
                        self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                        return False, error_msg
                else:
                    print(f"❌ 文件未创建: {temp_file}")
                    # 添加原始URL到错误信息
                    error_msg = f'下载失败: 视频文件未创建，可能是网页未解析出视频下载地址或下载过程中断\n\n原始URL: {url}'
                    self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                    return False, error_msg
            except Exception as e:
                print(f"❌ 阶段4失败: 检查文件错误")
                print(f"   错误详情: {str(e)}")
                raise Exception(f'检查下载结果失败: {str(e)}')
            
            # 阶段5: 转码为mov格式
            print(f"🎬 阶段5: 转码为mov格式")
            try:
                self.redis.update_task_status(task_id, 'transcoding', progress=0)
                print(f"✅ 任务状态已更新: transcoding")
                
                success, message = self.transcoder.transcode_video(temp_file, output_path, task_id)
                
                if success:
                    print(f"✅ 转码成功: {output_path}")
                    os.remove(temp_file)
                    print(f"✅ 临时文件已删除: {temp_file}")
                    self.redis.update_task_status(task_id, 'completed', progress=100, save_path=output_path)
                    print(f"✅ 任务状态已更新: completed")
                    print("=" * 60)
                    print(f"✅ 下载任务完成")
                    print("=" * 60)
                    return True, '下载成功'
                else:
                    print(f"❌ 阶段5失败: 转码失败")
                    print(f"   错误详情: {message}")
                    # 添加视频URL到错误信息
                    error_msg = f'转码失败: {message}\n\n解析的视频URL: {video_url}'
                    self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                    return False, error_msg
            except Exception as e:
                print(f"❌ 阶段5失败: 转码过程错误")
                print(f"   错误详情: {str(e)}")
                print(f"   错误类型: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                # 添加视频URL到错误信息
                error_msg = f'转码失败: {str(e)}\n\n解析的视频URL: {video_url}'
                self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                return False, error_msg
                
        except Exception as e:
            print("=" * 60)
            print(f"❌ 下载任务失败")
            print(f"   错误阶段: 未知")
            print(f"   错误详情: {str(e)}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print("=" * 60)
            # 添加视频URL到错误信息
            error_msg = f'下载失败: {str(e)}\n\n解析的视频URL: {video_url}'
            self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
            return False, error_msg
    
    def _download_douyin_manual(self, url, task_id, output_path):
        """手动下载抖音视频（备用方案）"""
        try:
            print(f'Downloading douyin video with manual method: {url}')
            
            video_info = self.parser.parse_video_info(url)
            video_url = video_info.get('video_url')
            
            if not video_url:
                raise Exception('无法获取视频下载链接')
            
            print(f'Video URL: {video_url[:100]}...')
            
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.douyin.com'
            headers['Origin'] = 'https://www.douyin.com'
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=600)  # 10分钟超时
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            start_time = time.time()
            last_update_time = start_time
            
            safe_filename = self._get_safe_filename(video_info.get('title', 'video'))
            temp_file = os.path.join(os.path.dirname(output_path), f"{safe_filename}.mp4")
            
            print(f'Saving to: {temp_file}')
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        current_time = time.time()
                        if current_time - last_update_time >= 1:
                            elapsed_time = current_time - start_time
                            if elapsed_time > 0:
                                speed = downloaded_size / elapsed_time
                                speed_str = self._format_speed(speed)
                                self.redis.update_task_download_speed(task_id, speed_str)
                            last_update_time = current_time
                        if total_size > 0:
                            progress = int(downloaded_size / total_size * 100)
                            self.redis.update_task_status(task_id, 'downloading', progress=progress)
            
            if os.path.exists(temp_file):
                self.redis.update_task_status(task_id, 'transcoding', progress=0)
                success, message = self.transcoder.transcode_video(temp_file, output_path, task_id)
                
                if success:
                    os.remove(temp_file)
                    self.redis.update_task_status(task_id, 'completed', progress=100, save_path=output_path)
                    return True, '下载成功'
                else:
                    # 添加视频URL到错误信息
                    error_msg = f'转码失败: {message}\n\n解析的视频URL: {video_url}'
                    self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                    return False, error_msg
            else:
                # 添加视频URL到错误信息
                error_msg = f'下载失败: 视频文件未找到，可能是网页未解析出视频下载地址\n\n解析的视频URL: {video_url}'
                self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                return False, error_msg
                
        except Exception as e:
            print(f'Error downloading douyin video: {e}')
            import traceback
            traceback.print_exc()
            # 添加视频URL到错误信息
            error_msg = f'下载失败: {str(e)}\n\n解析的视频URL: {video_url}'
            self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
            return False, error_msg
    
    def _get_safe_filename(self, title):
        import re
        import hashlib
        
        title = re.sub(r'[^\w\s\-\.#]', '', title)
        title = re.sub(r'[\s]+', '_', title.strip())
        
        max_filename_length = 80
        max_path_length = 500
        
        if len(title) > max_filename_length:
            title_hash = hashlib.md5(title.encode()).hexdigest()[:6]
            title = f"{title[:max_filename_length-15]}_{title_hash}"
        
        return title
    
    def _ytdlp_progress_hook(self, d, task_id):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and 'downloaded_bytes' in d:
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.redis.update_task_status(task_id, 'downloading', progress=progress)
                
                if 'speed' in d:
                    speed_str = self._format_speed(d['speed'])
                    self.redis.update_task_download_speed(task_id, speed_str)
        elif d['status'] == 'finished':
            print(f'Download finished for task {task_id}')
    
    def _parse_cookie_string(self, cookie_str):
        """解析Cookie字符串为yt-dlp可用的格式"""
        if not cookie_str:
            return None
        
        # yt-dlp可以直接接受Cookie字符串
        return cookie_str
    
    def download_video(self, url, task_id, storage_path):
        try:
            self._log(task_id, "========== 开始下载任务 ==========")
            self._log(task_id, f"URL: {url}")
            self._log(task_id, f"存储路径: {storage_path}")
            
            import os
            
            # 阶段1: 检测平台
            self._log(task_id, "阶段1: 检测视频平台")
            try:
                if 'douyin.com' in url or 'v.douyin.com' in url:
                    platform = 'douyin'
                elif 'bilibili.com' in url:
                    platform = 'bilibili'
                elif 'toutiao.com' in url:
                    platform = 'toutiao'
                else:
                    platform = 'unknown'
                self._log(task_id, f"✅ 平台检测完成: {platform}")
            except Exception as e:
                self._log(task_id, f"❌ 阶段1失败: 平台检测错误 - {str(e)}")
                raise Exception(f'平台检测失败: {str(e)}')
            
            # 抖音平台直接使用yt-dlp下载，不经过parser
            if platform == 'douyin':
                self._log(task_id, "📱 检测到抖音平台，使用yt-dlp直接下载")
                
                # 阶段2: 创建输出目录
                self._log(task_id, "阶段2: 创建输出目录")
                try:
                    safe_title = self._get_safe_filename('douyin_video')
                    video_dir = os.path.join(storage_path, platform, safe_title)
                    os.makedirs(video_dir, exist_ok=True)
                    self._log(task_id, f"✅ 目录创建成功: {video_dir}")
                except Exception as e:
                    self._log(task_id, f"❌ 阶段2失败: 目录创建错误 - {str(e)}")
                    raise Exception(f'目录创建失败: {str(e)}')
                
                mov_path = os.path.join(video_dir, f"{safe_title}.mov")
                self._log(task_id, f"📄 输出路径: {mov_path}")
                
                # 阶段3: 更新任务状态
                self._log(task_id, "阶段3: 更新任务状态")
                try:
                    self.redis.update_task_status(task_id, 'downloading', progress=0)
                    self._log(task_id, "✅ 任务状态已更新: downloading")
                except Exception as e:
                    self._log(task_id, f"❌ 阶段3失败: 更新状态错误 - {str(e)}")
                    raise Exception(f'更新状态失败: {str(e)}')
                
                # 阶段4: 获取Cookie
                self._log(task_id, "阶段4: 获取抖音Cookie")
                try:
                    cookie_data = self.redis.get_cookie('douyin')
                    if cookie_data and 'cookie' in cookie_data:
                        self._log(task_id, f"✅ Cookie已获取 (长度: {len(cookie_data['cookie'])})")
                    else:
                        self._log(task_id, "⚠️  未找到Cookie，将尝试无Cookie下载")
                except Exception as e:
                    self._log(task_id, f"❌ 阶段4失败: 获取Cookie错误 - {str(e)}")
                    self._log(task_id, "   ⚠️  将继续尝试无Cookie下载")
                    cookie_data = None
                
                # 阶段5: 调用抖音下载
                self._log(task_id, "阶段5: 调用抖音下载")
                
                # 使用video_scraper解析抖音视频信息
                try:
                    headers = self.headers.copy()
                    if cookie_data and 'cookie' in cookie_data:
                        headers['Cookie'] = cookie_data['cookie']
                        self._log(task_id, "✅ 使用Cookie进行解析")
                    
                    video_info = self.scraper.scrape_video(url, cookie_data)
                    
                    if not video_info or 'video_url' not in video_info or not video_info['video_url']:
                        self._log(task_id, "❌ 无法获取抖音视频下载链接")
                        raise Exception('无法获取抖音视频下载链接')
                    
                    video_url = video_info['video_url']
                    self._log(task_id, f"✅ 成功获取视频下载链接: {video_url[:100]}...")
                    
                    # 直接下载视频文件
                    self._log(task_id, "📥 开始下载视频文件...")
                    temp_file = os.path.join(video_dir, f"{safe_title}.mp4")
                    response = requests.get(video_url, headers=headers, timeout=600, stream=True)  # 10分钟超时
                    response.raise_for_status()
                    
                    # 保存视频文件
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(temp_file)
                    self._log(task_id, f"✅ 视频下载完成，文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                    
                    # 转码为mov格式
                    self._log(task_id, "阶段6: 转码为mov格式")
                    self.redis.update_task_status(task_id, 'transcoding', progress=0)
                    self._log(task_id, "✅ 任务状态已更新: transcoding")
                    success, message = self.transcoder.transcode_video(temp_file, mov_path, task_id)
                    
                    if success:
                        os.remove(temp_file)
                        self.redis.update_task_status(task_id, 'completed', progress=100, save_path=mov_path)
                        self._log(task_id, f"✅ 下载任务完成: {mov_path}")
                        return True, '下载成功'
                    else:
                        self._log(task_id, f"❌ 阶段6失败: 转码失败 - {message}")
                        error_msg = f'转码失败: {message}\n\n解析的视频URL: {video_url}'
                        self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                        return False, error_msg
                        
                except Exception as e:
                    self._log(task_id, f"❌ 阶段5失败: 抖音下载错误 - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    video_url = video_info.get('video_url', 'N/A') if 'video_info' in locals() else 'N/A'
                    error_msg = f'抖音下载失败: {str(e)}\n\n解析的视频URL: {video_url}'
                    self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                    return False, error_msg
            
            # 其他平台使用原有的parser逻辑
            # 阶段2: 解析视频信息
            print(f"🔍 阶段2: 解析视频信息")
            try:
                video_info = self.parser.parse_video_info(url)
                print(f"✅ 视频信息解析成功")
                print(f"   标题: {video_info.get('title', 'N/A')}")
                print(f"   平台: {video_info.get('platform', 'N/A')}")
            except Exception as e:
                print(f"❌ 阶段2失败: 视频信息解析错误")
                print(f"   错误详情: {str(e)}")
                print(f"   错误类型: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                raise Exception(f'视频信息解析失败: {str(e)}')
            
            # 阶段3: 更新任务状态
            print(f"📊 阶段3: 更新任务状态")
            try:
                self.redis.update_task_status(
                    task_id, 
                    'downloading',
                    progress=0
                )
                print(f"✅ 任务状态已更新: downloading")
            except Exception as e:
                print(f"❌ 阶段3失败: 更新状态错误")
                print(f"   错误详情: {str(e)}")
                raise Exception(f'更新状态失败: {str(e)}')
            
            platform = video_info['platform']
            cookie_data = self.redis.get_cookie(platform)
            
            title = video_info['title']
            video_url = video_info['video_url']
            audio_url = video_info.get('audio_url')
            
            import os
            platform_dir = os.path.join(storage_path, platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            # 使用安全文件名创建目录
            safe_title = self._get_safe_filename(title)
            video_dir = os.path.join(platform_dir, safe_title)
            os.makedirs(video_dir, exist_ok=True)
            
            mov_filename = f"{safe_title}.mov"
            mov_path = os.path.join(video_dir, mov_filename)
            
            if platform == 'douyin':
                return self._download_douyin_with_ytdlp(url, task_id, mov_path)
            
            video_filename = f"{safe_title}.mp4"
            video_path = os.path.join(video_dir, video_filename)
            
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.bilibili.com'
            headers['Origin'] = 'https://www.bilibili.com'
            headers['Accept'] = '*/*'
            headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['Connection'] = 'keep-alive'
            headers['Sec-Fetch-Dest'] = 'empty'
            headers['Sec-Fetch-Mode'] = 'cors'
            headers['Sec-Fetch-Site'] = 'same-site'
            if cookie_data:
                if platform == 'bilibili' and 'SESSDATA' in cookie_data:
                    headers['Cookie'] = f'SESSDATA={cookie_data["SESSDATA"]}'
                elif platform in ['douyin', 'toutiao'] and 'cookie' in cookie_data:
                    headers['Cookie'] = cookie_data['cookie']
            
            if audio_url:
                audio_filename = f"{safe_title}_audio.m4a"
                audio_path = os.path.join(video_dir, audio_filename)
                
                response_audio = requests.get(audio_url, headers=headers, stream=True, timeout=600)  # 10分钟超时
                response_audio.raise_for_status()
                
                total_audio_size = int(response_audio.headers.get('content-length', 0))
                downloaded_audio_size = 0
                
                with open(audio_path, 'wb') as f:
                    for chunk in response_audio.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_audio_size += len(chunk)
                
                response = requests.get(video_url, headers=headers, stream=True, timeout=600)  # 10分钟超时
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                start_time = time.time()
                last_update_time = start_time
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            current_time = time.time()
                            if current_time - last_update_time >= 1:
                                elapsed_time = current_time - start_time
                                if elapsed_time > 0:
                                    speed = downloaded_size / elapsed_time
                                    speed_str = self._format_speed(speed)
                                    self.redis.update_task_download_speed(task_id, speed_str)
                                last_update_time = current_time
                            if total_size > 0:
                                progress = int(downloaded_size / total_size * 50)
                                self.redis.update_task_status(task_id, 'downloading', progress=progress)
                
                import subprocess
                merged_filename = f"{safe_title}_merged.mp4"
                merged_path = os.path.join(video_dir, merged_filename)
                
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-i', audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-y',
                    merged_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                
                if os.path.exists(merged_path):
                    os.remove(video_path)
                    os.remove(audio_path)
                    os.rename(merged_path, video_path)
            else:
                response = requests.get(video_url, headers=headers, stream=True, timeout=600)  # 10分钟超时
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                start_time = time.time()
                last_update_time = start_time
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            current_time = time.time()
                            if current_time - last_update_time >= 1:
                                elapsed_time = current_time - start_time
                                if elapsed_time > 0:
                                    speed = downloaded_size / elapsed_time
                                    speed_str = self._format_speed(speed)
                                    self.redis.update_task_download_speed(task_id, speed_str)
                                last_update_time = current_time
                            if total_size > 0:
                                progress = int(downloaded_size / total_size * 100)
                                self.redis.update_task_status(task_id, 'downloading', progress=progress)
            
            if os.path.exists(video_path):
                self.redis.update_task_status(task_id, 'transcoding', progress=0)
                success, message = self.transcoder.transcode_video(video_path, mov_path, task_id)
                
                if success:
                    os.remove(video_path)
                    self.redis.update_task_status(task_id, 'completed', progress=100, save_path=mov_path)
                    return True, '下载成功'
                else:
                    # 添加视频URL到错误信息
                    error_msg = f'转码失败: {message}\n\n解析的视频URL: {video_url}'
                    self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                    return False, error_msg
            else:
                # 添加视频URL到错误信息
                error_msg = f'下载失败: 视频文件未找到，可能是网页未解析出视频下载地址\n\n解析的视频URL: {video_url}'
                self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
                return False, error_msg
            
        except Exception as e:
            # 添加视频URL到错误信息
            error_msg = f'下载失败: {str(e)}\n\n解析的视频URL: {video_url}'
            self.redis.update_task_status(task_id, 'failed', error_message=error_msg)
            return False, error_msg