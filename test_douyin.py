#!/usr/bin/env python3
import sys
sys.path.append('/Users/rockfile/Documents/Bytedance/BusinessProj/AutoDownloadVideoApp')

from video_scraper import VideoScraper

def test_douyin_url():
    test_url = 'https://v.douyin.com/IBBnrqQWO10/'
    
    print('测试抖音短链接解析')
    print('=' * 60)
    print(f'测试链接: {test_url}')
    print()
    
    scraper = VideoScraper()
    
    try:
        result = scraper.scrape_video(test_url)
        
        print('✅ 解析成功!')
        print()
        print('视频信息:')
        print(f'  标题: {result.get("title")}')
        print(f'  平台: {result.get("platform")}')
        print(f'  视频ID: {result.get("video_id")}')
        print(f'  视频类型: {result.get("video_type")}')
        print(f'  视频URL: {result.get("video_url")[:50] if result.get("video_url") else "无"}...')
        print()
        
        return True
        
    except Exception as e:
        print(f'❌ 解析失败: {str(e)}')
        print()
        return False

if __name__ == '__main__':
    success = test_douyin_url()
    sys.exit(0 if success else 1)