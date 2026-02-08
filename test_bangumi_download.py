#!/usr/bin/env python3
import sys
sys.path.append('/Users/rockfile/Documents/Bytedance/BusinessProj/AutoDownloadVideoApp')

from redis_manager import RedisManager
from video_downloader import VideoDownloader
from datetime import datetime
import os

def test_bangumi_download():
    test_url = 'https://www.bilibili.com/bangumi/play/ep316163/?share_source=copy_web'
    storage_path = '/Users/rockfile/Downloads/Videos'
    
    print('测试Bilibili番剧完整下载流程')
    print('=' * 60)
    print(f'测试链接: {test_url}')
    print(f'存储路径: {storage_path}')
    print()
    
    redis_manager = RedisManager()
    downloader = VideoDownloader(redis_manager)
    
    try:
        print('步骤1: 解析视频信息...')
        video_info = downloader.parser.parse_video_info(test_url)
        print(f'✅ 解析成功')
        print(f'  标题: {video_info.get("title")}')
        print(f'  视频类型: {video_info.get("video_type")}')
        print(f'  视频URL: {video_info.get("video_url")[:80] if video_info.get("video_url") else "无"}...')
        print()
        
        print('步骤2: 创建下载任务...')
        import uuid
        task_id = str(uuid.uuid4())
        task_data = {
            'id': task_id,
            'url': test_url,
            'title': video_info.get('title'),
            'platform': video_info.get('platform'),
            'video_type': video_info.get('video_type'),
            'status': 'pending',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        redis_manager.set_task(task_id, task_data)
        print(f'✅ 任务创建成功，任务ID: {task_id}')
        print()
        
        print('步骤3: 开始下载...')
        success, message = downloader.download_video(test_url, task_id, storage_path)
        
        if success:
            print(f'✅ 下载成功: {message}')
            
            task = redis_manager.get_task(task_id)
            if task:
                print(f'  任务状态: {task.get("status")}')
                print(f'  保存路径: {task.get("save_path")}')
                print(f'  进度: {task.get("progress", 0)}%')
        else:
            print(f'❌ 下载失败: {message}')
        
        print()
        return success
        
    except Exception as e:
        print(f'❌ 测试失败: {str(e)}')
        import traceback
        traceback.print_exc()
        print()
        return False

if __name__ == '__main__':
    success = test_bangumi_download()
    sys.exit(0 if success else 1)