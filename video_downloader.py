import requests
import re
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import yt_dlp
from video_scraper import VideoScraper

class VideoParser:
    def __init__(self):
        self.platform_patterns = {
            'bilibili': [
                r'b23\.tv/([a-zA-Z0-9]+)',
                r'bilibili\.com/video/([a-zA-Z0-9]+)',
                r'bilibili\.com/video/BV([a-zA-Z0-9]+)'
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
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _format_speed(self, speed_bytes):
        if speed_bytes < 1024:
            return f'{speed_bytes:.2f} B/s'
        elif speed_bytes < 1024 * 1024:
            return f'{speed_bytes / 1024:.2f} KB/s'
        elif speed_bytes < 1024 * 1024 * 1024:
            return f'{speed_bytes / (1024 * 1024):.2f} MB/s'
        else:
            return f'{speed_bytes / (1024 * 1024 * 1024):.2f} GB/s'
    
    def download_video(self, url, task_id, storage_path):
        try:
            video_info = self.parser.parse_video_info(url)
            
            self.redis.update_task_status(
                task_id, 
                'downloading',
                progress=0
            )
            
            platform = video_info['platform']
            cookie_data = self.redis.get_cookie(platform)
            
            title = video_info['title']
            video_url = video_info['video_url']
            audio_url = video_info.get('audio_url')
            
            import os
            platform_dir = os.path.join(storage_path, platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            video_dir = os.path.join(platform_dir, title)
            os.makedirs(video_dir, exist_ok=True)
            
            video_filename = f"{title}.mp4"
            video_path = os.path.join(video_dir, video_filename)
            
            headers = self.headers.copy()
            if cookie_data:
                if platform == 'bilibili' and 'SESSDATA' in cookie_data:
                    headers['Cookie'] = f'SESSDATA={cookie_data["SESSDATA"]}'
                elif platform in ['douyin', 'toutiao'] and 'cookie' in cookie_data:
                    headers['Cookie'] = cookie_data['cookie']
            
            if audio_url:
                audio_filename = f"{title}_audio.m4a"
                audio_path = os.path.join(video_dir, audio_filename)
                
                response_audio = requests.get(audio_url, headers=headers, stream=True, timeout=30)
                response_audio.raise_for_status()
                
                total_audio_size = int(response_audio.headers.get('content-length', 0))
                downloaded_audio_size = 0
                
                with open(audio_path, 'wb') as f:
                    for chunk in response_audio.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_audio_size += len(chunk)
                
                response = requests.get(video_url, headers=headers, stream=True, timeout=30)
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
                merged_filename = f"{title}_merged.mp4"
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
                response = requests.get(video_url, headers=headers, stream=True, timeout=30)
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
            
            self.redis.update_task_status(task_id, 'completed', progress=100, save_path=video_path)
            
            return True, '下载成功'
            
        except Exception as e:
            self.redis.update_task_status(task_id, 'failed')
            return False, f'下载失败: {str(e)}'