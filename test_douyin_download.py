#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_downloader import VideoDownloader
from redis_manager import RedisManager

def test_douyin_download():
    print("=" * 60)
    print("🧪 测试抖音视频下载功能")
    print("=" * 60)
    
    redis = RedisManager()
    downloader = VideoDownloader(redis)
    
    test_url = "https://v.douyin.com/IBBnrqQWO10/"
    task_id = "test_task_001"
    output_path = "/Users/rockfile/Downloads/Videos/douyin/test_video.mov"
    
    print(f"测试URL: {test_url}")
    print(f"输出路径: {output_path}")
    print("-" * 60)
    
    try:
        success, message = downloader.download_video(test_url, task_id, "/Users/rockfile/Downloads/Videos")
        
        print("-" * 60)
        if success:
            print("✅ 下载测试成功！")
            print(f"结果: {message}")
            
            # 检查文件是否存在
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ 文件已创建: {output_path}")
                print(f"文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
            else:
                print("❌ 文件未创建")
        else:
            print("❌ 下载测试失败！")
            print(f"错误信息: {message}")
            
    except Exception as e:
        print(f"❌ 测试过程发生异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_douyin_download()