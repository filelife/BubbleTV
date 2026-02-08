#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本模板

所有测试脚本都应该继承此模板，确保使用测试数据库
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.redis_manager import RedisManager
from backend.core.video_downloader import VideoParser, VideoDownloader
from backend.core.video_scraper import VideoScraper
from backend.core.video_transcoder import VideoTranscoder
from backend.platforms.platform_auth import PlatformAuth
from backend.core.storage_manager import StorageManager

# ⚠️ 重要：所有测试必须使用测试数据库！
# 使用 use_test_db=True 来确保测试和生产环境隔离
TEST_REDIS_MANAGER = RedisManager(use_test_db=True)

def setup_test_environment():
    """设置测试环境"""
    print("=" * 60)
    print("🧪 设置测试环境")
    print("=" * 60)
    print("⚠️  使用测试数据库 (DB=1)")
    print("⚠️  不影响生产环境 (DB=0)")
    print("=" * 60)

def cleanup_test_tasks():
    """清理测试任务"""
    print("\n🧹 清理测试任务...")
    tasks = TEST_REDIS_MANAGER.get_all_tasks()
    
    if len(tasks) == 0:
        print("✅ 没有需要清理的测试任务")
        return
    
    deleted_count = 0
    for task in tasks:
        if TEST_REDIS_MANAGER.delete_task(task['id']):
            deleted_count += 1
    
    print(f"✅ 清理完成，共删除 {deleted_count} 个测试任务")

def run_test():
    """运行测试（子类覆盖此方法）"""
    print("❌ 请覆盖 run_test() 方法")
    return False

def main():
    """主函数"""
    setup_test_environment()
    
    try:
        success = run_test()
        if success:
            print("\n✅ 测试通过")
        else:
            print("\n❌ 测试失败")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试任务
        cleanup_test_tasks()

if __name__ == '__main__':
    main()