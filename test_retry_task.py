#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重试任务功能
"""

import requests
import json
import time

BASE_URL = 'http://192.168.31.226:5001'

def test_retry_task():
    print("=" * 60)
    print("🧪 测试重试任务功能")
    print("=" * 60)
    
    # 步骤1：创建一个抖音任务
    print("\n📝 步骤1：创建一个抖音任务")
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
    
    # 步骤2：等待任务失败
    print(f"\n⏳ 步骤2：等待任务失败...")
    time.sleep(10)
    
    # 步骤3：获取任务状态
    print(f"\n📋 步骤3：获取任务状态")
    response = requests.get(f'{BASE_URL}/api/tasks')
    result = response.json()
    
    if result.get('success'):
        tasks = result.get('tasks', [])
        
        # 查找我们创建的任务
        found_task = None
        for task in tasks:
            if task.get('id') == task_id:
                found_task = task
                print(f"✅ 找到任务: {task.get('title')}")
                print(f"   状态: {task.get('status')}")
                if task.get('error_message'):
                    print(f"   错误信息: {task.get('error_message')}")
                break
        
        if not found_task:
            print(f"❌ 未找到任务 {task_id}")
            return
        
        # 步骤4：重试任务
        if found_task.get('status') == 'failed':
            print(f"\n🔄 步骤4：重试任务")
            response = requests.post(f'{BASE_URL}/api/tasks/{task_id}/retry')
            result = response.json()
            
            if result.get('success'):
                print(f"✅ 任务重试成功")
            else:
                print(f"❌ 任务重试失败: {result.get('message')}")
        else:
            print(f"\n⚠️  任务状态为: {found_task.get('status')}，不是failed状态，无法重试")
    else:
        print(f"❌ 获取任务列表失败: {result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_retry_task()