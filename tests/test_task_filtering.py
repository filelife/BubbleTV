#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务列表过滤功能
"""

import requests
import json
import time

BASE_URL = 'http://192.168.31.226:5001'

def test_task_filtering():
    print("=" * 60)
    print("🧪 测试任务列表过滤功能")
    print("=" * 60)
    
    # 步骤1：创建一个任务
    print("\n📝 步骤1：创建一个测试任务")
    create_data = {
        'url': 'https://v.douyin.com/IBBnrqQWO10/'
    }
    
    response = requests.post(f'{BASE_URL}/api/tasks', json=create_data)
    result = response.json()
    
    if result.get('success'):
        task_id = result.get('task_id')
        print(f"✅ 任务创建成功，任务ID: {task_id}")
    else:
        print(f"❌ 任务创建失败: {result.get('message')}")
        return
    
    # 步骤2：获取任务列表，确认任务存在
    print(f"\n📋 步骤2：获取任务列表")
    response = requests.get(f'{BASE_URL}/api/tasks')
    result = response.json()
    
    if result.get('success'):
        tasks = result.get('tasks', [])
        print(f"✅ 获取任务列表成功，任务数量: {len(tasks)}")
        
        # 查找我们创建的任务
        found_task = None
        for task in tasks:
            if task.get('id') == task_id:
                found_task = task
                print(f"✅ 找到任务: {task.get('title')}")
                break
        
        if not found_task:
            print(f"❌ 未找到任务 {task_id}")
    else:
        print(f"❌ 获取任务列表失败: {result.get('message')}")
        return
    
    # 步骤3：删除任务
    print(f"\n🗑️  步骤3：删除任务 {task_id}")
    response = requests.delete(f'{BASE_URL}/api/tasks/{task_id}')
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 任务删除成功")
    else:
        print(f"❌ 任务删除失败: {result.get('message')}")
        return
    
    # 步骤4：再次获取任务列表，确认任务已被过滤
    print(f"\n📋 步骤4：再次获取任务列表")
    time.sleep(1)  # 等待1秒，确保删除操作完成
    
    response = requests.get(f'{BASE_URL}/api/tasks')
    result = response.json()
    
    if result.get('success'):
        tasks = result.get('tasks', [])
        print(f"✅ 获取任务列表成功，任务数量: {len(tasks)}")
        
        # 查找我们删除的任务
        found_task = None
        for task in tasks:
            if task.get('id') == task_id:
                found_task = task
                print(f"❌ 任务 {task_id} 仍然存在于列表中（不应该出现）")
                break
        
        if not found_task:
            print(f"✅ 任务 {task_id} 已被正确过滤，不再显示")
    else:
        print(f"❌ 获取任务列表失败: {result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_task_filtering()