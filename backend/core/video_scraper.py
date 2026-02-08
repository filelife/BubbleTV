import requests
import re
import json
from urllib.parse import urlparse, parse_qs
import time
import random

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class VideoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_video(self, url, cookie_data=None):
        platform = self._detect_platform(url)
        
        if platform == 'bilibili':
            return self._scrape_bilibili(url, cookie_data)
        elif platform == 'douyin':
            return self._scrape_douyin(url, cookie_data)
        elif platform == 'toutiao':
            return self._scrape_toutiao(url, cookie_data)
        else:
            raise ValueError('不支持的视频平台')
    
    def _detect_platform(self, url):
        if 'bilibili.com' in url or 'b23.tv' in url:
            return 'bilibili'
        elif 'douyin.com' in url:
            return 'douyin'
        elif 'toutiao.com' in url:
            return 'toutiao'
        return None
    
    def _scrape_bilibili(self, url, cookie_data=None):
        try:
            headers = self.headers.copy()
            if cookie_data and 'SESSDATA' in cookie_data:
                headers['Cookie'] = f'SESSDATA={cookie_data["SESSDATA"]}'
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.encoding = 'utf-8'
            
            title = self._extract_bilibili_title(response.text)
            video_id = self._extract_bilibili_id(url)
            
            if not video_id:
                raise ValueError('无法提取Bilibili视频ID')
            
            if video_id.startswith('EP'):
                return self._scrape_bilibili_bangumi(url, video_id, headers, title)
            
            api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={video_id}'
            api_response = requests.get(api_url, headers=headers, timeout=15)
            api_data = api_response.json()
            
            if api_data.get('code') != 0:
                raise ValueError(f'Bilibili API错误: {api_data.get("message", "未知错误")}')
            
            video_info = api_data['data']
            title = video_info.get('title', title)
            
            cid = video_info.get('cid')
            if not cid:
                pages = video_info.get('pages', [])
                if pages:
                    cid = pages[0].get('cid')
            
            if not cid:
                raise ValueError('无法获取Bilibili视频CID')
            
            play_url_api = f'https://api.bilibili.com/x/player/playurl?bvid={video_id}&cid={cid}&qn=80&fnval=16&fourk=1'
            play_response = requests.get(play_url_api, headers=headers, timeout=15)
            play_data = play_response.json()
            
            if play_data.get('code') != 0:
                error_msg = play_data.get('message', '未知错误')
                if play_data.get('code') == -404:
                    raise ValueError('视频不存在或已被删除')
                elif play_data.get('code') == -403:
                    raise ValueError('需要登录才能下载此视频')
                else:
                    raise ValueError(f'Bilibili播放URL获取失败: {error_msg}')
            
            play_info = play_data.get('data', {})
            durl = play_info.get('durl', [])
            
            video_url = None
            audio_url = None
            
            if durl:
                video_url = durl[0].get('url')
            
            if not video_url:
                dash_data = play_info.get('dash', {})
                if dash_data:
                    video_list = dash_data.get('video', [])
                    audio_list = dash_data.get('audio', [])
                    
                    if video_list:
                        video_url = video_list[0].get('baseUrl')
                    
                    if audio_list:
                        audio_url = audio_list[0].get('baseUrl')
            
            if not video_url:
                raise ValueError('无法获取Bilibili视频下载链接，可能需要登录或视频受版权保护')
            
            return {
                'title': title,
                'platform': 'bilibili',
                'url': url,
                'video_url': video_url,
                'audio_url': audio_url,
                'video_id': video_id,
                'cid': cid,
                'video_type': '短视频'
            }
            
        except Exception as e:
            raise Exception(f'Bilibili视频爬取失败: {str(e)}')
    
    def _scrape_bilibili_bangumi(self, url, ep_id, headers, title):
        try:
            ep_match = re.search(r'ep([0-9]+)', url)
            if not ep_match:
                raise ValueError('无法提取番剧EP ID')
            
            ep_id_num = ep_match.group(1)
            
            api_url = f'https://api.bilibili.com/pgc/player/web/v2/playurl?ep_id={ep_id_num}&qn=80&fnval=16&fourk=1'
            play_response = requests.get(api_url, headers=headers, timeout=15)
            play_data = play_response.json()
            
            if play_data.get('code') != 0:
                error_msg = play_data.get('message', '未知错误')
                if play_data.get('code') == -404:
                    raise ValueError('番剧不存在或已被删除')
                elif play_data.get('code') == -403:
                    raise ValueError('需要大会员才能下载此番剧')
                else:
                    raise ValueError(f'Bilibili番剧播放URL获取失败: {error_msg}')
            
            result = play_data.get('result', {})
            if not result:
                raise ValueError('番剧API返回空结果，可能需要大会员')
            
            video_info = result.get('video_info', {})
            if not video_info:
                raise ValueError('番剧视频信息为空')
            
            durl = video_info.get('durl', [])
            
            video_url = None
            audio_url = None
            
            if durl:
                video_url = durl[0].get('url')
            
            if not video_url:
                dash_data = video_info.get('dash', {})
                if dash_data:
                    video_list = dash_data.get('video', [])
                    audio_list = dash_data.get('audio', [])
                    
                    if video_list:
                        video_url = video_list[0].get('baseUrl')
                    
                    if audio_list:
                        audio_url = audio_list[0].get('baseUrl')
            
            if not video_url:
                raise ValueError('无法获取Bilibili番剧下载链接，可能需要大会员或番剧受版权保护')
            
            return {
                'title': title,
                'platform': 'bilibili',
                'url': url,
                'video_url': video_url,
                'audio_url': audio_url,
                'video_id': ep_id,
                'video_type': '番剧'
            }
            
        except Exception as e:
            raise Exception(f'Bilibili番剧爬取失败: {str(e)}')
    
    def _extract_bilibili_title(self, html):
        title_patterns = [
            r'<title>([^<]+)</title>',
            r'"title":"([^"]+)"',
            r'h1[^>]*>([^<]+)</h1>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html)
            if match:
                title = match.group(1).strip()
                title = title.replace('_哔哩哔哩_bilibili', '').replace('- 哔哩哔哩', '')
                return title
        
        return '未知标题'
    
    def _extract_bilibili_id(self, url):
        bv_match = re.search(r'BV([a-zA-Z0-9]+)', url)
        if bv_match:
            return 'BV' + bv_match.group(1)
        
        ep_match = re.search(r'ep([0-9]+)', url)
        if ep_match:
            return self._resolve_bilibili_bangumi_url(ep_match.group(1))
        
        short_match = re.search(r'b23\.tv/([a-zA-Z0-9]+)', url)
        if short_match:
            return self._resolve_bilibili_short_url(short_match.group(1))
        
        return None
    
    def _resolve_bilibili_bangumi_url(self, ep_id):
        try:
            api_url = f'https://api.bilibili.com/pgc/player/web/v2/playurl?ep_id={ep_id}'
            response = requests.get(api_url, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get('code') == 0:
                result = data.get('result', {})
                if result:
                    return f'EP{ep_id}'
        except:
            pass
        return f'EP{ep_id}'
    
    def _resolve_bilibili_short_url(self, short_code):
        try:
            response = requests.get(f'https://b23.tv/{short_code}', headers=self.headers, timeout=10, allow_redirects=False)
            location = response.headers.get('Location', '')
            bv_match = re.search(r'BV([a-zA-Z0-9]+)', location)
            if bv_match:
                return 'BV' + bv_match.group(1)
        except:
            pass
        return None
    
    def _resolve_douyin_short_url(self, short_code):
        try:
            print(f'Resolving short URL: https://v.douyin.com/{short_code}')
            response = requests.get(f'https://v.douyin.com/{short_code}', headers=self.headers, timeout=10, allow_redirects=True)
            final_url = response.url
            print(f'Redirected to: {final_url}')
            
            match = re.search(r'/video/(\d+)', final_url)
            if match:
                print(f'Found video ID in final URL: {match.group(1)}')
                return match.group(1)
            
            match = re.search(r'/(\d+)/', final_url)
            if match:
                print(f'Found video ID in final URL: {match.group(1)}')
                return match.group(1)
            
            print('No video ID found in final URL')
            return None
        except Exception as e:
            print(f'Error resolving short URL: {e}')
            return None
    
    def _scrape_douyin(self, url, cookie_data=None):
        try:
            print(f'Using yt-dlp for douyin video scraping: {url}')
            
            headers = self.headers.copy()
            if cookie_data and 'cookie' in cookie_data:
                headers['Cookie'] = cookie_data['cookie']
            
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': False,
                'extract_flat': False,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'cookiefile': None,
                'nocheckcertificate': True,
                'ignoreerrors': True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        title = info.get('title', '未知标题')
                        video_url = info.get('url')
                        
                        if not video_url:
                            raise ValueError('无法获取视频下载链接')
                        
                        return {
                            'title': title,
                            'platform': 'douyin',
                            'url': url,
                            'video_url': video_url,
                            'video_id': info.get('id', ''),
                            'video_type': '短视频'
                        }
                    else:
                        raise ValueError('无法获取视频信息')
                        
            except Exception as ytdlp_error:
                print(f'yt-dlp error: {ytdlp_error}')
                
                # 如果yt-dlp不可用，直接跳过到回退方法
                if yt_dlp is None:
                    print('yt-dlp not available, falling back to manual scraping method...')
                else:
                    print('Falling back to manual scraping method...')
                return self._scrape_douyin_fallback(url, headers)
            
        except Exception as e:
            raise Exception(f'抖音视频爬取失败: {str(e)}')
    
    def _scrape_douyin_fallback(self, url, headers):
        title = '未知标题'
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.encoding = 'utf-8'
            
            print(f'Response URL: {response.url}')
            print(f'Response status: {response.status_code}')
            
            title = self._extract_douyin_title(response.text)
            
            item_ids = self._extract_douyin_item_ids(response.text)
            print(f'Found item IDs: {item_ids}')
            
            # 如果从HTML中提取失败，尝试从URL中提取
            if not item_ids:
                print('No item IDs found in HTML, trying to extract from URL...')
                video_id = self._extract_douyin_video_id(url)
                if video_id:
                    item_ids = [video_id]
                    print(f'Extracted item ID from URL: {video_id}')
                else:
                    raise ValueError(f'无法从HTML或URL中获取视频ID (网页标题: {title})')
            
            item_id = item_ids[0]
            print(f'Using item ID: {item_id}')
            
            video_url = self._extract_douyin_video_url_from_html(response.text)
            if not video_url:
                print('No video URL found in HTML, trying API method...')
                video_url = self._get_douyin_video_url_from_api(item_id, headers)
            
            if not video_url:
                raise ValueError(f'无法获取抖音视频下载链接 (网页标题: {title})')
            
            return {
                'title': title,
                'platform': 'douyin',
                'url': url,
                'video_url': video_url,
                'video_id': item_id,
                'video_type': '短视频'
            }
            
        except Exception as e:
            error_msg = str(e)
            if title and '网页标题' not in error_msg:
                error_msg = f'{error_msg} (网页标题: {title})'
            raise Exception(f'抖音视频回退爬取失败: {error_msg}')
    
    def _extract_douyin_title(self, html):
        title_patterns = [
            r'<title>([^<]+)</title>',
            r'"desc":"([^"]+)"',
            r'"title":"([^"]+)"'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html)
            if match:
                title = match.group(1).strip()
                title = title.replace('- 抖音', '').replace('抖音', '')
                return title
        
        return '未知标题'
    
    def _extract_douyin_real_video_url(self, item_id, headers):
        try:
            print(f'Fetching real video URL for item_id: {item_id}')
            
            api_url = f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={item_id}'
            
            print(f'API URL: {api_url}')
            
            api_headers = headers.copy()
            api_headers.update({
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.douyin.com/',
                'X-Baidu-Server-Token': 'test',
                'X-SS-Request-Id': 'test'
            })
            
            api_response = requests.get(api_url, headers=api_headers, timeout=15)
            api_response.raise_for_status()
            
            print(f'API Response status: {api_response.status_code}')
            
            try:
                api_data = api_response.json()
                print(f'API Data keys: {api_data.keys() if isinstance(api_data, dict) else "Not a dict"}')
                
                if 'aweme_detail' in api_data:
                    aweme = api_data['aweme_detail']
                    if 'video' in aweme:
                        video = aweme['video']
                        if 'play_addr' in video:
                            urls = video['play_addr']['url_list']
                            if urls and len(urls) > 0:
                                real_url = urls[0]['url']
                                print(f'Found real video URL: {real_url[:100]}...')
                                return real_url
                        if 'download_addr' in video:
                            urls = video['download_addr']['url_list']
                            if urls and len(urls) > 0:
                                real_url = urls[0]['url']
                                print(f'Found download URL: {real_url[:100]}...')
                                return real_url
                
                if 'aweme_list' in api_data and api_data['aweme_list']:
                    aweme = api_data['aweme_list'][0]
                    if 'video' in aweme:
                        video = aweme['video']
                        if 'play_addr' in video:
                            urls = video['play_addr']['url_list']
                            if urls and len(urls) > 0:
                                real_url = urls[0]['url']
                                print(f'Found real video URL: {real_url[:100]}...')
                                return real_url
                
                print('No video URL found in API response')
                return None
                
            except ValueError as e:
                print(f'JSON parsing error: {e}')
                return None
                
        except Exception as e:
            print(f'Error fetching real video URL: {e}')
            return None
    
    def _extract_douyin_video_id(self, url):
        print(f'Extracting video ID from URL: {url}')
        match = re.search(r'/video/(\d+)', url)
        if match:
            print(f'Found video ID from /video/ pattern: {match.group(1)}')
            return match.group(1)
        
        match = re.search(r'/(\d+)/', url)
        if match:
            print(f'Found video ID from /(\d+)/ pattern: {match.group(1)}')
            return match.group(1)
        
        match = re.search(r'v\.douyin\.com/([a-zA-Z0-9]+)', url)
        if match:
            short_code = match.group(1)
            print(f'Found short code: {short_code}, resolving...')
            resolved_id = self._resolve_douyin_short_url(short_code)
            print(f'Resolved video ID: {resolved_id}')
            return resolved_id
        
        print('No video ID found')
        return None
    
    def _extract_douyin_item_ids(self, html):
        patterns = [
            r'"aweme_id":"(\d+)"',
            r'"item_ids":\["(\d+)"\]',
            r'"itemId":"(\d+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                return matches
        
        return []
    
    def _extract_douyin_video_url(self, api_data):
        try:
            if isinstance(api_data, dict):
                if 'item_list' in api_data:
                    items = api_data['item_list']
                    if items and len(items) > 0:
                        item = items[0]
                        if 'video' in item:
                            video = item['video']
                            if 'play_addr' in video:
                                urls = video['play_addr']['url_list']
                                if urls and len(urls) > 0:
                                    return urls[0]['url']
                            if 'download_addr' in video:
                                urls = video['download_addr']['url_list']
                                if urls and len(urls) > 0:
                                    return urls[0]['url']
                
                if 'aweme_details' in api_data:
                    details = api_data['aweme_details']
                    if details and len(details) > 0:
                        detail = details[0]
                        if 'video' in detail:
                            video = detail['video']
                            if 'play_addr' in video:
                                urls = video['play_addr']['url_list']
                                if urls and len(urls) > 0:
                                    return urls[0]['url']
            
            return None
        except Exception as e:
            return None
    
    def _extract_douyin_video_url_from_html(self, html):
        try:
            print(f'Extracting video URL from HTML, length: {len(html)}')
            
            # 首先尝试从HTML中提取渲染数据 (SSR)
            ssr_patterns = [
                r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.*?})</script>',
                r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
                r'<script[^>]*>window\.__data\s*=\s*({.*?})</script>',
            ]
            
            for pattern in ssr_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    print(f'Found SSR data in HTML')
                    try:
                        import json
                        data = json.loads(match.group(1))
                        print(f'SSR data keys: {list(data.keys())[:5] if isinstance(data, dict) else "N/A"}')
                        
                        # 尝试从SSR数据中提取视频URL
                        video_url = self._extract_from_ssr_data(data)
                        if video_url:
                            print(f'Found video URL from SSR data: {video_url[:100]}...')
                            return video_url
                    except Exception as e:
                        print(f'Error parsing SSR data: {e}')
            
            # 尝试从JSON-LD中提取
            jsonld_pattern = r'<script type="application/ld\+json">({.*?})</script>'
            jsonld_matches = re.findall(jsonld_pattern, html, re.DOTALL)
            for jsonld_str in jsonld_matches:
                try:
                    import json
                    data = json.loads(jsonld_str)
                    if 'contentUrl' in data:
                        url = data['contentUrl']
                        if self._is_valid_video_url(url):
                            print(f'Found video URL from JSON-LD: {url[:100]}...')
                            return url
                except Exception as e:
                    print(f'Error parsing JSON-LD: {e}')
            
            # 尝试从meta标签中提取
            meta_patterns = [
                r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"',
                r'<meta[^>]*property="og:video:url"[^>]*content="([^"]+)"',
                r'<meta[^>]*name="twitter:player:stream"[^>]*content="([^"]+)"',
            ]
            for pattern in meta_patterns:
                match = re.search(pattern, html)
                if match:
                    url = match.group(1)
                    if self._is_valid_video_url(url):
                        print(f'Found video URL from meta tag: {url[:100]}...')
                        return url
            
            # 尝试匹配视频URL模式 (优先匹配视频流URL)
            video_patterns = [
                # 优先匹配douyinvod视频流
                r'https://[^"\s<>]*douyinvod\.com[^"\s<>]*\.mp4[^"\s<>]*',
                r'https://[^"\s<>]*amemv\.com[^"\s<>]*\.mp4[^"\s<>]*',
                r'https://[^"\s<>]*byteimg\.com[^"\s<>]*\.mp4[^"\s<>]*',
                # 通用mp4
                r'https?://[^"\s<>]+\.mp4[^"\s<>]*',
                # play_addr模式
                r'"play_addr":\{[^}]*"url_list":\[[^]]*"url":"([^"]+)"',
                r'"download_addr":\{[^}]*"url_list":\[[^]]*"url":"([^"]+)"',
            ]
            
            for i, pattern in enumerate(video_patterns):
                matches = re.findall(pattern, html)
                if matches:
                    print(f'Found match with pattern {i}')
                    for url in matches:
                        url = url.replace('\\u0026', '&').replace('\\u003D', '=').replace('\\', '').replace('"', '')
                        if url.startswith('http'):
                            if 'monitor' in url or 'collect' in url or 'batch' in url:
                                print(f'Skipping monitor API URL: {url[:100]}...')
                                continue
                            # 检查是否是真实的视频URL
                            if self._is_valid_video_url(url):
                                print(f'Extracted video URL: {url[:100]}...')
                                return url
                            else:
                                print(f'Skipping invalid URL: {url[:100]}...')
            
            # 最后尝试查找所有URL
            all_urls = re.findall(r'https?://[^\s"\'<>]+', html)
            print(f'Found {len(all_urls)} total URLs in HTML')
            for url in all_urls:
                if 'monitor' in url or 'collect' in url or 'batch' in url:
                    continue
                if '.mp4' in url or '.m3u8' in url or 'douyinvod' in url:
                    url = url.replace('\\u0026', '&').replace('\\u003D', '=').replace('\\', '')
                    if self._is_valid_video_url(url):
                        print(f'Found video URL: {url[:100]}...')
                        return url
            
            print('No video URL found in HTML')
            return None
        except Exception as e:
            print(f'Error extracting video URL from HTML: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_from_ssr_data(self, data):
        """从SSR数据中提取视频URL"""
        try:
            if isinstance(data, dict):
                # 尝试不同的路径
                paths = [
                    ['app', 'videoDetail', 'video', 'playAddr', 'urlList', 0, 'url'],
                    ['app', 'videoDetail', 'video', 'downloadAddr', 'urlList', 0, 'url'],
                    ['aweme', 'detail', 'video', 'play_addr', 'url_list', 0, 'url'],
                    ['aweme_detail', 'video', 'play_addr', 'url_list', 0, 'url'],
                ]
                
                for path in paths:
                    current = data
                    for key in path:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                            current = current[key]
                        else:
                            current = None
                            break
                    
                    if current and isinstance(current, str) and current.startswith('http'):
                        return current
            
            return None
        except Exception as e:
            print(f'Error extracting from SSR data: {e}')
            return None
    
    def _is_valid_video_url(self, url):
        """检查URL是否是有效的视频URL"""
        if not url or not isinstance(url, str):
            return False
        
        # 排除网页URL
        invalid_patterns = [
            r'/video/\d+$',  # 抖音视频页面
            r'/share/video/',  # 分享页面
            r'www\.douyin\.com/video/',  # 抖音网页
            r'iesdouyin\.com/share/',  # 分享页面
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, url):
                return False
        
        # 必须是有效的视频流URL
        valid_patterns = [
            r'\.mp4',
            r'\.m3u8',
            r'video.*\.douyinvod\.com',
            r'v.*\.douyinvod\.com',
            r'api.*\.amemv\.com',
        ]
        
        for pattern in valid_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _get_douyin_video_url_from_api(self, item_id, headers):
        """通过抖音API获取视频URL"""
        try:
            print(f'Trying to get video URL from API for item_id: {item_id}')
            
            # 尝试多个API端点
            api_urls = [
                f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={item_id}',
                f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={item_id}',
            ]
            
            for api_url in api_urls:
                print(f'Trying API: {api_url}')
                try:
                    api_headers = headers.copy()
                    api_headers.update({
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Referer': 'https://www.douyin.com/',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                        'X-Requested-With': 'XMLHttpRequest',
                    })
                    
                    # 添加session来保持cookies
                    session = requests.Session()
                    api_response = session.get(api_url, headers=api_headers, timeout=10)
                    print(f'API response status: {api_response.status_code}')
                    print(f'API response content length: {len(api_response.text)}')
                    print(f'API response content preview: {api_response.text[:200]}...')
                    
                    if api_response.status_code == 200:
                        # 检查内容是否为空
                        if not api_response.text or api_response.text.strip() == '':
                            print('API response is empty')
                            continue
                        
                        # 检查是否是JSON格式
                        content_type = api_response.headers.get('Content-Type', '')
                        print(f'Content-Type: {content_type}')
                        
                        if 'json' not in content_type.lower():
                            print(f'API did not return JSON, got: {content_type}')
                            # 可能是HTML错误页面或重定向
                            if '<html' in api_response.text.lower():
                                print('API returned HTML instead of JSON')
                            continue
                        
                        try:
                            api_data = api_response.json()
                            print(f'API data type: {type(api_data)}')
                            print(f'API data keys: {list(api_data.keys()) if isinstance(api_data, dict) else "N/A"}')
                            
                            if isinstance(api_data, dict):
                                # 尝试提取视频URL
                                video_url = self._extract_douyin_video_url(api_data)
                                if video_url:
                                    print(f'Found video URL from API: {video_url[:100]}...')
                                    return video_url
                        except Exception as e:
                            print(f'Error parsing API response: {e}')
                            continue
                            
                except Exception as e:
                    print(f'Error with API {api_url}: {e}')
                    continue
            
            print('All API methods failed')
            
            # 尝试第三方解析服务
            print('Trying third-party parsing service...')
            video_url = self._get_douyin_video_from_third_party(item_id)
            if video_url:
                print(f'Found video URL from third-party: {video_url[:100]}...')
                return video_url
            
            return None
            
        except Exception as e:
            print(f'Error in _get_douyin_video_url_from_api: {e}')
            return None
    
    def _get_douyin_video_from_third_party(self, item_id):
        """使用第三方抖音视频解析服务"""
        try:
            # 尝试多个第三方解析服务
            parser_urls = [
                f'https://api.douyin.wtf/api?url=https://www.douyin.com/video/{item_id}',
                f'https://douyin.wtf/api?url=https://www.douyin.com/video/{item_id}',
                f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={item_id}',
                f'https://api.peark.com/api/douyin/video?url=https://www.douyin.com/video/{item_id}',
                f'https://api.52dyc.cn/douyin/api?url=https://www.douyin.com/video/{item_id}',
            ]
            
            for parser_url in parser_urls:
                print(f'Trying third-party parser: {parser_url}')
                try:
                    response = requests.get(parser_url, timeout=10)
                    print(f'Third-party response status: {response.status_code}')
                    print(f'Third-party response content length: {len(response.text)}')
                    print(f'Third-party response preview: {response.text[:200]}...')
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f'Third-party data type: {type(data)}')
                            print(f'Third-party data keys: {list(data.keys()) if isinstance(data, dict) else "N/A"}')
                            
                            # 尝试多种可能的字段名
                            possible_keys = ['url', 'video_url', 'data', 'video', 'play_url', 'play_addr']
                            for key in possible_keys:
                                if key in data:
                                    video_url = data[key]
                                    if isinstance(video_url, str) and video_url.startswith('http'):
                                        if self._is_valid_video_url(video_url):
                                            print(f'Found video URL from third-party (key={key}): {video_url[:100]}...')
                                            return video_url
                                    elif isinstance(video_url, dict) and 'url' in video_url:
                                        if self._is_valid_video_url(video_url['url']):
                                            print(f'Found video URL from third-party (nested): {video_url["url"][:100]}...')
                                            return video_url['url']
                                    
                        except Exception as e:
                            print(f'Error parsing third-party response: {e}')
                            import traceback
                            traceback.print_exc()
                            continue
                except Exception as e:
                    print(f'Error with third-party parser: {e}')
                    continue
            
            print('All third-party parsers failed')
            return None
            
        except Exception as e:
            print(f'Error in _get_douyin_video_from_third_party: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def _scrape_toutiao(self, url, cookie_data=None):
        try:
            headers = self.headers.copy()
            if cookie_data and 'cookie' in cookie_data:
                headers['Cookie'] = cookie_data['cookie']
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.encoding = 'utf-8'
            
            title = self._extract_toutiao_title(response.text)
            video_id = self._extract_toutiao_video_id(url)
            
            if not video_id:
                raise ValueError('无法提取今日头条视频ID')
            
            item_id = self._extract_toutiao_item_id(response.text)
            if not item_id:
                raise ValueError('无法获取今日头条视频信息')
            
            api_url = f'https://www.toutiao.com/video/article/v2/article_info/?item_id={item_id}'
            api_response = requests.get(api_url, headers=headers, timeout=15)
            
            if api_response.status_code != 200:
                raise ValueError('今日头条API请求失败')
            
            try:
                api_data = api_response.json()
            except:
                raise ValueError('今日头条API返回数据格式错误')
            
            video_url = self._extract_toutiao_video_url(api_data)
            if not video_url:
                raise ValueError('无法获取今日头条视频下载链接')
            
            return {
                'title': title,
                'platform': 'toutiao',
                'url': url,
                'video_url': video_url,
                'video_id': item_id,
                'video_type': '短视频'
            }
            
        except Exception as e:
            raise Exception(f'今日头条视频爬取失败: {str(e)}')
    
    def _extract_toutiao_title(self, html):
        title_patterns = [
            r'<title>([^<]+)</title>',
            r'"title":"([^"]+)"',
            r'"article_title":"([^"]+)"'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html)
            if match:
                title = match.group(1).strip()
                title = title.replace('- 今日头条', '').replace('今日头条', '')
                return title
        
        return '未知标题'
    
    def _extract_toutiao_video_id(self, url):
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        match = re.search(r'/is/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_toutiao_item_id(self, html):
        patterns = [
            r'"item_id":"(\d+)"',
            r'"article_id":"(\d+)"',
            r'"group_id":"(\d+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_toutiao_video_url(self, api_data):
        try:
            if isinstance(api_data, dict):
                if 'data' in api_data:
                    data = api_data['data']
                    if isinstance(data, dict):
                        if 'video_info' in data:
                            video_info = data['video_info']
                            if 'video_url' in video_info:
                                return video_info['video_url']
                            if 'play_url' in video_info:
                                return video_info['play_url']
            
            return None
        except Exception as e:
            return None