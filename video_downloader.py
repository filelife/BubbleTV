import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import yt_dlp

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
        platform = self.detect_platform(url)
        if not platform:
            raise ValueError('不支持的视频平台')
        
        video_type = self.detect_video_type(url, platform)
        
        try:
            if platform == 'bilibili':
                return self._parse_bilibili(url)
            elif platform == 'douyin':
                return self._parse_douyin(url)
            elif platform == 'toutiao':
                return self._parse_toutiao(url)
        except Exception as e:
            raise Exception(f'解析视频信息失败: {str(e)}')
    
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
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{storage_path}/{platform}/{video_info["title"]}/%(title)s.%(ext)s',
                'cookiefile': None,
                'progress_hooks': [lambda d: self._progress_hook(d, task_id)],
            }
            
            if cookie_data:
                ydl_opts['cookiefile'] = self._create_cookie_file(cookie_data, platform)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.redis.update_task_status(task_id, 'completed', progress=100)
            
            return True, '下载成功'
            
        except Exception as e:
            self.redis.update_task_status(task_id, 'failed')
            return False, f'下载失败: {str(e)}'
    
    def _progress_hook(self, d, task_id):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.redis.update_task_status(task_id, 'downloading', progress=progress)
    
    def _create_cookie_file(self, cookie_data, platform):
        import tempfile
        cookie_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        
        for key, value in cookie_data.items():
            cookie_file.write(f'{platform}\tTRUE\t/{key}\tTRUE\n')
        
        cookie_file.close()
        return cookie_file.name