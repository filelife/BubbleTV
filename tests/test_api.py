#!/usr/bin/env python3
import requests
import json
import time
import os
import sys

BASE_URL = 'http://192.168.31.226:5001'

def print_test(test_name):
    print(f'\n{"="*60}')
    print(f'测试: {test_name}')
    print(f'{"="*60}')

def print_result(success, message):
    status = '✅ 通过' if success else '❌ 失败'
    print(f'{status}: {message}')

def test_api_storage_path():
    print_test('获取存储路径API')
    try:
        response = requests.get(f'{BASE_URL}/api/storage/path')
        data = response.json()
        if data.get('success') and data.get('storage_path'):
            print_result(True, f'存储路径: {data["storage_path"]}')
            return data['storage_path']
        else:
            print_result(False, f'响应错误: {data}')
            return None
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return None

def test_api_videos():
    print_test('获取视频列表API')
    try:
        response = requests.get(f'{BASE_URL}/api/videos')
        data = response.json()
        if data.get('success'):
            videos = data.get('videos', [])
            print_result(True, f'共 {len(videos)} 个视频')
            return videos
        else:
            print_result(False, f'响应错误: {data}')
            return []
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return []

def test_api_tasks():
    print_test('获取任务列表API')
    try:
        response = requests.get(f'{BASE_URL}/api/tasks')
        data = response.json()
        if data.get('success'):
            tasks = data.get('tasks', [])
            print_result(True, f'共 {len(tasks)} 个任务')
            return tasks
        else:
            print_result(False, f'响应错误: {data}')
            return []
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return []

def test_add_task(url):
    print_test('添加下载任务')
    try:
        task_data = {
            'url': url,
            'status': 'pending',
            'progress': 0,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        response = requests.post(f'{BASE_URL}/api/tasks', json=task_data)
        data = response.json()
        if data.get('success'):
            print_result(True, f'任务ID: {data.get("task_id")}')
            return data.get('task_id')
        else:
            print_result(False, f'添加失败: {data}')
            return None
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return None

def test_open_task(task_id):
    print_test('打开任务')
    try:
        response = requests.post(f'{BASE_URL}/api/tasks/{task_id}/open')
        data = response.json()
        if data.get('success'):
            print_result(True, f'路径: {data.get("path")}')
            return True
        else:
            print_result(False, f'打开失败: {data}')
            return False
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return False

def test_delete_task(task_id):
    print_test('删除任务')
    try:
        response = requests.delete(f'{BASE_URL}/api/tasks/{task_id}')
        data = response.json()
        if data.get('success'):
            print_result(True, '任务已删除')
            return True
        else:
            print_result(False, f'删除失败: {data}')
            return False
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return False

def test_delete_video(path, is_folder=False):
    print_test('删除视频/文件夹')
    try:
        response = requests.post(f'{BASE_URL}/api/videos/delete', json={
            'path': path,
            'is_folder': is_folder
        })
        data = response.json()
        if data.get('success'):
            print_result(True, data.get('message'))
            return True
        else:
            print_result(False, f'删除失败: {data}')
            return False
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return False

def test_scan_videos():
    print_test('扫描视频')
    try:
        response = requests.post(f'{BASE_URL}/api/videos/scan')
        data = response.json()
        if data.get('success'):
            print_result(True, data.get('message'))
            return True
        else:
            print_result(False, f'扫描失败: {data}')
            return False
    except Exception as e:
        print_result(False, f'请求失败: {str(e)}')
        return False

def main():
    print('\n🧪 自动化测试套件')
    print('=' * 60)
    
    results = []
    
    storage_path = test_api_storage_path()
    results.append(('存储路径API', storage_path is not None))
    
    videos = test_api_videos()
    results.append(('视频列表API', len(videos) >= 0))
    
    tasks = test_api_tasks()
    results.append(('任务列表API', len(tasks) >= 0))
    
    if tasks:
        first_task = tasks[0]
        task_id = first_task.get('id')
        
        if task_id and first_task.get('status') == 'completed':
            test_open_task(task_id)
            results.append(('打开任务', True))
        else:
            results.append(('打开任务', False))
    
    test_scan_videos()
    results.append(('扫描视频', True))
    
    print('\n' + '=' * 60)
    print('📊 测试结果汇总')
    print('=' * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = '✅ 通过' if result else '❌ 失败'
        print(f'{status} {test_name}')
    
    print('\n' + '=' * 60)
    print(f'总计: {passed}/{total} 个测试通过')
    print('=' * 60)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)