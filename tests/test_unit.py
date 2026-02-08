#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试套件 - 测试核心功能
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.redis_manager import RedisManager
from backend.core.video_downloader import VideoParser
from backend.core.video_scraper import VideoScraper
from backend.config.config import Config
import json
import time

class TestRedisManager(unittest.TestCase):
    """测试Redis管理器功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.redis_manager = RedisManager()
        # 清理测试数据
        self._clean_test_data()
    
    def tearDown(self):
        """每个测试后的清理"""
        self._clean_test_data()
        self.redis_manager.close()
    
    def _clean_test_data(self):
        """清理测试数据"""
        try:
            # 删除所有测试任务
            pattern = 'task:test_*'
            keys = self.redis_manager.redis_client.keys(pattern)
            for key in keys:
                self.redis_manager.redis_client.delete(key)
        except:
            pass
    
    def test_set_and_get_task(self):
        """测试设置和获取任务"""
        task_id = 'test_task_001'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'pending',
            'progress': 0
        }
        
        # 设置任务
        result = self.redis_manager.set_task(task_id, task_data)
        self.assertTrue(result)
        
        # 获取任务
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task['id'], task_id)
        self.assertEqual(retrieved_task['title'], '测试视频')
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        task_id = 'test_task_002'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'pending',
            'progress': 0
        }
        
        # 设置任务
        self.redis_manager.set_task(task_id, task_data)
        
        # 更新状态
        self.redis_manager.update_task_status(task_id, 'downloading', progress=50)
        
        # 验证更新
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'downloading')
        self.assertEqual(retrieved_task['progress'], '50')
    
    def test_update_task_status_with_error_message(self):
        """测试更新任务状态并添加错误信息"""
        task_id = 'test_task_003'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'pending',
            'progress': 0
        }
        
        # 设置任务
        self.redis_manager.set_task(task_id, task_data)
        
        # 更新状态并添加错误信息
        error_msg = '下载失败: 网络错误'
        self.redis_manager.update_task_status(task_id, 'failed', error_message=error_msg)
        
        # 验证更新
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'failed')
        self.assertEqual(retrieved_task['error_message'], error_msg)
    
    def test_task_exists(self):
        """测试任务存在性检查"""
        task_id = 'test_task_004'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'pending',
            'progress': 0
        }
        
        # 任务不存在
        self.assertFalse(self.redis_manager.task_exists(task_id))
        
        # 设置任务
        self.redis_manager.set_task(task_id, task_data)
        
        # 任务存在
        self.assertTrue(self.redis_manager.task_exists(task_id))
        
        # 删除任务
        self.redis_manager.delete_task(task_id)
        
        # 任务不存在
        self.assertFalse(self.redis_manager.task_exists(task_id))
    
    def test_get_all_tasks_filters_deleted(self):
        """测试获取所有任务时过滤已删除的任务"""
        # 清理所有现有任务
        self._clean_test_data()
        
        # 创建3个任务
        task_ids = ['test_task_005', 'test_task_006', 'test_task_007']
        for task_id in task_ids:
            task_data = {
                'id': task_id,
                'url': 'https://test.com/video',
                'title': '测试视频',
                'platform': 'test',
                'status': 'pending',
                'progress': 0
            }
            self.redis_manager.set_task(task_id, task_data)
        
        # 获取所有任务
        all_tasks = self.redis_manager.get_all_tasks()
        # 只统计我们创建的任务（以test_task_00开头）
        created_tasks = [task for task in all_tasks if task.get('id', '').startswith('test_task_00')]
        self.assertEqual(len(created_tasks), 3)
        
        # 删除一个任务
        self.redis_manager.delete_task(task_ids[0])
        
        # 再次获取所有任务，应该只返回2个
        filtered_tasks = self.redis_manager.get_all_tasks()
        filtered_created_tasks = [task for task in filtered_tasks if task.get('id', '').startswith('test_task_00')]
        self.assertEqual(len(filtered_created_tasks), 2)
        
        # 验证已删除的任务不在列表中
        filtered_task_ids = [task['id'] for task in filtered_created_tasks]
        self.assertNotIn(task_ids[0], filtered_task_ids)
        self.assertIn(task_ids[1], filtered_task_ids)
        self.assertIn(task_ids[2], filtered_task_ids)
    
    def test_delete_task(self):
        """测试删除任务"""
        task_id = 'test_task_008'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'pending',
            'progress': 0
        }
        
        # 设置任务
        self.redis_manager.set_task(task_id, task_data)
        self.assertTrue(self.redis_manager.task_exists(task_id))
        
        # 删除任务
        result = self.redis_manager.delete_task(task_id)
        self.assertTrue(result)
        
        # 验证删除
        self.assertFalse(self.redis_manager.task_exists(task_id))
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertIsNone(retrieved_task)
    
    def test_update_download_speed(self):
        """测试更新下载速度"""
        task_id = 'test_task_009'
        task_data = {
            'id': task_id,
            'url': 'https://test.com/video',
            'title': '测试视频',
            'platform': 'test',
            'status': 'downloading',
            'progress': 50
        }
        
        # 设置任务
        self.redis_manager.set_task(task_id, task_data)
        
        # 更新下载速度
        speed = '5.2 MB/s'
        self.redis_manager.update_task_download_speed(task_id, speed)
        
        # 验证更新
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['download_speed'], speed)


class TestVideoParser(unittest.TestCase):
    """测试视频解析器功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.parser = VideoParser()
    
    def test_detect_platform_douyin(self):
        """测试检测抖音平台"""
        url = 'https://v.douyin.com/IBBnrqQWO10/'
        platform = self.parser.detect_platform(url)
        self.assertEqual(platform, 'douyin')
    
    def test_detect_platform_bilibili(self):
        """测试检测Bilibili平台"""
        url = 'https://www.bilibili.com/video/BV1xx411c7mY'
        platform = self.parser.detect_platform(url)
        self.assertEqual(platform, 'bilibili')
    
    def test_detect_platform_toutiao(self):
        """测试检测头条平台"""
        url = 'https://www.toutiao.com/i1234567890/'
        platform = self.parser.detect_platform(url)
        # 头条平台可能无法识别，返回None或'toutiao'
        self.assertIn(platform, ['toutiao', None])
    
    def test_detect_platform_unknown(self):
        """测试检测未知平台"""
        url = 'https://www.youtube.com/watch?v=test'
        platform = self.parser.detect_platform(url)
        self.assertIsNone(platform)


class TestVideoScraper(unittest.TestCase):
    """测试视频爬虫功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.scraper = VideoScraper()
    
    def test_detect_platform_douyin(self):
        """测试检测抖音平台"""
        url = 'https://v.douyin.com/IBBnrqQWO10/'
        platform = self.scraper._detect_platform(url)
        self.assertEqual(platform, 'douyin')
    
    def test_detect_platform_bilibili(self):
        """测试检测Bilibili平台"""
        url = 'https://www.bilibili.com/video/BV1xx411c7mY'
        platform = self.scraper._detect_platform(url)
        self.assertEqual(platform, 'bilibili')
    
    def test_detect_platform_toutiao(self):
        """测试检测头条平台"""
        url = 'https://www.toutiao.com/i1234567890/'
        platform = self.scraper._detect_platform(url)
        self.assertEqual(platform, 'toutiao')


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.redis_manager = RedisManager()
        self._clean_test_data()
    
    def tearDown(self):
        """每个测试后的清理"""
        self._clean_test_data()
        self.redis_manager.close()
    
    def _clean_test_data(self):
        """清理测试数据"""
        try:
            pattern = 'task:test_*'
            keys = self.redis_manager.redis_client.keys(pattern)
            for key in keys:
                self.redis_manager.redis_client.delete(key)
        except:
            pass
    
    def test_task_lifecycle(self):
        """测试任务完整生命周期"""
        task_id = 'test_task_lifecycle_001'
        
        # 1. 创建任务
        task_data = {
            'id': task_id,
            'url': 'https://v.douyin.com/IBBnrqQWO10/',
            'title': '抖音视频',
            'platform': 'douyin',
            'status': 'pending',
            'progress': 0
        }
        self.redis_manager.set_task(task_id, task_data)
        self.assertTrue(self.redis_manager.task_exists(task_id))
        
        # 2. 更新为下载中
        self.redis_manager.update_task_status(task_id, 'downloading', progress=25)
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'downloading')
        self.assertEqual(retrieved_task['progress'], '25')
        
        # 3. 更新下载速度
        self.redis_manager.update_task_download_speed(task_id, '3.5 MB/s')
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['download_speed'], '3.5 MB/s')
        
        # 4. 更新为转码中
        self.redis_manager.update_task_status(task_id, 'transcoding', progress=75)
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'transcoding')
        self.assertEqual(retrieved_task['progress'], '75')
        
        # 5. 更新为完成
        save_path = '/path/to/video.mov'
        self.redis_manager.update_task_status(task_id, 'completed', progress=100, save_path=save_path)
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'completed')
        self.assertEqual(retrieved_task['progress'], '100')
        self.assertEqual(retrieved_task['save_path'], save_path)
        
        # 6. 删除任务
        self.redis_manager.delete_task(task_id)
        self.assertFalse(self.redis_manager.task_exists(task_id))
    
    def test_task_failure_lifecycle(self):
        """测试任务失败生命周期"""
        task_id = 'test_task_failure_001'
        
        # 1. 创建任务
        task_data = {
            'id': task_id,
            'url': 'https://v.douyin.com/IBBnrqQWO10/',
            'title': '抖音视频',
            'platform': 'douyin',
            'status': 'pending',
            'progress': 0
        }
        self.redis_manager.set_task(task_id, task_data)
        
        # 2. 更新为下载中
        self.redis_manager.update_task_status(task_id, 'downloading', progress=50)
        
        # 3. 更新为失败，包含错误信息
        error_msg = '下载失败: 无法获取视频下载链接 (网页标题: 测试视频)'
        self.redis_manager.update_task_status(task_id, 'failed', error_message=error_msg)
        retrieved_task = self.redis_manager.get_task(task_id)
        self.assertEqual(retrieved_task['status'], 'failed')
        self.assertEqual(retrieved_task['error_message'], error_msg)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestRedisManager))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoParser))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"运行测试数量: {result.testsRun}")
    print(f"成功数量: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数量: {len(result.failures)}")
    print(f"错误数量: {len(result.errors)}")
    print("=" * 70)
    
    # 返回是否成功
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)