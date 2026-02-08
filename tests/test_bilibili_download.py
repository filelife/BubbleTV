#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试B站下载功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.redis_manager import RedisManager
from backend.core.video_downloader import VideoDownloader
from backend.config.config import Config

def test_bilibili_download():
    """测试B站下载"""
    print("=" * 60)
    print("🧪 开始测试B站下载")
    print("=" * 60)
    
    # 使用测试数据库
    redis = RedisManager(use_test_db=True)
    downloader = VideoDownloader(redis)
    
    # 测试URL
    url = "https://www.bilibili.com/video/BV1EV6dBpEa8/"
    task_id = "test_bilibili_001"
    storage_path = Config.DEFAULT_STORAGE_PATH
    
    print(f"📥 测试URL: {url}")
    print(f"🆔 任务ID: {task_id}")
    print(f"📁 存储路径: {storage_path}")
    print("=" * 60)
    
    try:
        # 执行下载
        success, message = downloader.download_video(url, task_id, storage_path)
        
        print("=" * 60)
        if success:
            print("✅ 测试成功")
            print(f"📄 消息: {message}")
        else:
            print("❌ 测试失败")
            print(f"📄 错误: {message}")
        print("=" * 60)
        
        # 获取任务日志
        logs = redis.get_task_logs(task_id)
        print(f"\n📋 任务日志 ({len(logs)}条):")
        print("=" * 60)
        for log in logs[:20]:  # 只显示前20条
            print(log)
        if len(logs) > 20:
            print(f"... 还有 {len(logs) - 20} 条日志")
        print("=" * 60)
        
        # 获取任务状态
        task = redis.get_task(task_id)
        if task:
            print(f"\n📊 任务状态:")
            print(f"   状态: {task.get('status')}")
            print(f"   进度: {task.get('progress')}%")
            if task.get('error_message'):
                print(f"   错误: {task.get('error_message')}")
        
    except Exception as e:
        print("=" * 60)
        print("❌ 测试异常")
        print(f"📄 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
    
    finally:
        redis.close()

if __name__ == '__main__':
    test_bilibili_download()
