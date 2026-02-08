#!/usr/bin/env python3
"""
抖音视频下载测试框架
专门用于验证抖音视频链接解析和下载逻辑
"""

import os
import sys
import unittest
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch
from backend.core.video_scraper import VideoScraper
from backend.core.video_downloader import VideoParser, VideoDownloader
from backend.core.video_transcoder import VideoTranscoder
from backend.core.redis_manager import RedisManager

class TestDouyinVideoDownload(unittest.TestCase):
    def setUp(self):
        self.parser = VideoParser()
        self.redis_manager = Mock()
        self.redis_manager.default_storage_path = '/Users/rockfile/Documents/Bytedance/BusinessProj/AutoDownloadVideoApp'
        self.downloader = VideoDownloader(self.redis_manager)
        self.transcoder = VideoTranscoder(self.redis_manager)
        
        # 失败案例测试集
        self.failed_test_cases = [
            {
                'name': '抖音短链接1',
                'url': 'https://v.douyin.com/nODnSd1_G4g/',
                'expected_platform': 'douyin',
                'description': '经典书籍预测精读'
            },
            {
                'name': '抖音短链接2', 
                'url': 'https://v.douyin.com/IBBnrqQWO10/',
                'expected_platform': 'douyin',
                'description': '上海房地产收储政策解读'
            },
            {
                'name': '抖音完整链接1',
                'url': 'https://www.douyin.com/video/7603635429073620275',
                'expected_platform': 'douyin',
                'description': '从短链接重定向后的完整链接'
            }
        ]
    
    def test_platform_detection(self):
        """测试平台检测功能"""
        print("\n=== 测试平台检测功能 ===")
        for case in self.failed_test_cases:
            print(f"\n测试案例: {case['name']}")
            print(f"URL: {case['url']}")
            
            try:
                platform = self.parser.detect_platform(case['url'])
                print(f"检测到的平台: {platform}")
                self.assertEqual(platform, case['expected_platform'])
                print("✅ 平台检测通过")
            except Exception as e:
                print(f"❌ 平台检测失败: {e}")
                self.fail(f"平台检测失败: {e}")
    
    def test_video_id_extraction(self):
        """测试视频ID提取功能"""
        print("\n=== 测试视频ID提取功能 ===")
        for case in self.failed_test_cases:
            print(f"\n测试案例: {case['name']}")
            print(f"URL: {case['url']}")
            
            try:
                video_id = self.scraper._extract_douyin_video_id(case['url'])
                print(f"提取的视频ID: {video_id}")
                if video_id:
                    self.assertTrue(len(video_id) > 0)
                    print("✅ 视频ID提取通过")
                else:
                    print("❌ 视频ID提取失败: 返回None")
            except Exception as e:
                print(f"❌ 视频ID提取异常: {e}")
    
    def test_html_content_extraction(self):
        """测试HTML内容提取功能"""
        print("\n=== 测试HTML内容提取功能 ===")
        for case in self.failed_test_cases:
            print(f"\n测试案例: {case['name']}")
            print(f"URL: {case['url']}")
            
            try:
                # 模拟获取HTML内容
                with patch('requests.get') as mock_get:
                    # 设置模拟响应
                    mock_response = Mock()
                    mock_response.text = '''
                    {
                        "aweme_detail": {
                            "aweme_id": "7603635429073620275",
                            "video": {
                                "play_addr": {
                                    "url_list": [
                                        {
                                            "url": "https://example.com/video.mp4"
                                        }
                                    ]
                                }
                            },
                            "desc": "测试视频标题"
                        }
                    }
                    '''
                    mock_response.url = case['url']
                    mock_response.status_code = 200
                    mock_get.return_value = mock_response
                    
                    # 测试item ID提取
                    item_ids = self.scraper._extract_douyin_item_ids(mock_response.text)
                    print(f"提取的item IDs: {item_ids}")
                    
                    if item_ids:
                        print("✅ HTML内容提取通过")
                    else:
                        print("❌ HTML内容提取失败: 未找到item IDs")
                        
            except Exception as e:
                print(f"❌ HTML内容提取异常: {e}")
    
    def test_video_url_extraction(self):
        """测试视频URL提取功能"""
        print("\n=== 测试视频URL提取功能 ===")
        
        # 模拟包含真实视频URL的HTML内容
        test_html_samples = [
            {
                'name': '标准JSON格式',
                'html': '''
                {
                    "aweme_detail": {
                        "video": {
                            "play_addr": {
                                "url_list": [
                                    {
                                        "url": "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7603635429073620275"
                                    }
                                ]
                            }
                        }
                    }
                }
                '''
            },
            {
                'name': '直接URL格式',
                'html': '''
                "play_addr":{"url_list":[{"url":"https://www.douyin.com/video/play/7603635429073620275"}]}
                '''
            },
            {
                'name': '网页URL格式（当前问题）',
                'html': '''
                "url":"https://www.douyin.com/video/7603635429073620275"
                '''
            }
        ]
        
        for sample in test_html_samples:
            print(f"\n测试样本: {sample['name']}")
            print(f"HTML内容长度: {len(sample['html'])}")
            
            try:
                video_url = self.scraper._extract_douyin_video_url_from_html(sample['html'])
                print(f"提取的视频URL: {video_url}")
                
                if video_url:
                    if '.mp4' in video_url or 'douyin.com' in video_url:
                        print("✅ 视频URL提取通过")
                    else:
                        print("⚠️ 提取到URL但格式可能不正确")
                else:
                    print("❌ 视频URL提取失败: 返回None")
            except Exception as e:
                print(f"❌ 视频URL提取异常: {e}")
    
    def test_download_simulation(self):
        """模拟下载过程测试"""
        print("\n=== 模拟下载过程测试 ===")
        
        for case in self.failed_test_cases:
            print(f"\n测试案例: {case['name']}")
            print(f"URL: {case['url']}")
            
            try:
                # 测试解析过程
                video_info = self.parser.parse_video_info(case['url'])
                print(f"解析的视频信息: {video_info}")
                
                if video_info:
                    print("✅ 视频信息解析通过")
                    
                    # 测试安全文件名生成
                    safe_filename = self.downloader._get_safe_filename(video_info.get('title', 'video'))
                    print(f"安全文件名: {safe_filename}")
                    self.assertTrue(len(safe_filename) <= 80)
                    print("✅ 安全文件名生成通过")
                    
                else:
                    print("❌ 视频信息解析失败")
                    
            except Exception as e:
                print(f"❌ 下载模拟测试异常: {e}")
                import traceback
                traceback.print_exc()
    
    def test_real_url_resolving(self):
        """测试真实URL解析"""
        print("\n=== 测试真实URL解析 ===")
        
        # 测试实际的URL解析过程
        test_url = 'https://v.douyin.com/nODnSd1_G4g/'
        
        try:
            print(f"解析URL: {test_url}")
            
            # 模拟短链接重定向
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.url = 'https://www.douyin.com/video/7603635429073620275?from_ssr=1'
                mock_response.status_code = 200
                mock_response.text = '''
                {
                    "aweme_detail": {
                        "aweme_id": "7603635429073620275",
                        "video": {
                            "play_addr": {
                                "url_list": [
                                    {
                                        "url": "https://example.com/real-video-url.mp4"
                                    }
                                ]
                            }
                        },
                        "desc": "经典书籍《预测》精读"
                    }
                }
                '''
                mock_get.return_value = mock_response
                
                video_info = self.scraper.parse_video_info(test_url)
                print(f"最终视频信息: {video_info}")
                
                if video_info and 'video_url' in video_info:
                    print("✅ 真实URL解析通过")
                else:
                    print("❌ 真实URL解析失败")
                    
        except Exception as e:
            print(f"❌ 真实URL解析异常: {e}")
            import traceback
            traceback.print_exc()

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 启动抖音视频下载综合测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDouyinVideoDownload)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print(f"总测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)