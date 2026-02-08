#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试任务（仅清理测试数据库，不影响生产环境）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_manager import RedisManager

def cleanup_test_tasks():
    print("=" * 60)
    print("🧹 清理测试任务（测试数据库）")
    print("=" * 60)
    
    # 使用测试数据库
    redis_manager = RedisManager(use_test_db=True)
    
    # 获取所有任务
    tasks = redis_manager.get_all_tasks()
    print(f"\n📋 测试数据库任务数量: {len(tasks)}")
    
    if len(tasks) == 0:
        print("✅ 没有需要清理的测试任务")
        return
    
    # 删除所有测试任务
    deleted_count = 0
    for task in tasks:
        task_id = task.get('id')
        task_title = task.get('title')
        task_status = task.get('status')
        
        print(f"\n🗑️  删除测试任务:")
        print(f"   ID: {task_id}")
        print(f"   标题: {task_title}")
        print(f"   状态: {task_status}")
        
        if redis_manager.delete_task(task_id):
            deleted_count += 1
            print(f"   ✅ 删除成功")
        else:
            print(f"   ❌ 删除失败")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 清理完成，共删除 {deleted_count} 个测试任务")
    print("⚠️  注意：此操作仅影响测试数据库，不影响生产环境")
    print("=" * 60)

if __name__ == '__main__':
    cleanup_test_tasks()