#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试错误信息中是否包含视频URL
"""

import requests
import json
import time

BASE_URL = 'http://192.168.31.226:5001'

def test_error_message_with_url():
    print("=" * 60)
    print("🧪 测试错误信息中是否包含视频URL")
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
    time.sleep(15)
    
    # 步骤3：获取任务状态，检查错误信息
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
                    error_message = task.get('error_message')
                    print(f"   错误信息:\n{error_message}")
                    
                    # 检查错误信息中是否包含URL
                    if 'URL' in error_message or 'url' in error_message:
                        print(f"\n✅ 错误信息中包含URL信息")
                    else:
                        print(f"\n❌ 错误信息中不包含URL信息")
                break
        
        if not found_task:
            print(f"❌ 未找到任务 {task_id}")
    else:
        print(f"❌ 获取任务列表失败: {result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n💡 请在浏览器中查看任务列表，确认错误信息中包含视频URL")
    print("💡 点击错误信息框中的'复制'按钮测试复制功能")

if __name__ == '__main__':
    test_error_message_with_url()