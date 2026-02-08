from flask import Flask, render_template, jsonify, request
from redis_manager import RedisManager
from video_downloader import VideoParser, VideoDownloader
from platform_auth import PlatformAuth
from video_transcoder import VideoTranscoder
from storage_manager import StorageManager
from config import Config
import uuid
import os
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

redis_manager = RedisManager()
video_parser = VideoParser()
video_downloader = VideoDownloader(redis_manager)
platform_auth = PlatformAuth(redis_manager)
video_transcoder = VideoTranscoder(redis_manager)
storage_manager = StorageManager(redis_manager)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = redis_manager.get_all_tasks()
        
        # 检查任务是否还存在，过滤掉已删除的任务
        valid_tasks = []
        for task in tasks:
            task_id = task.get('id')
            if task_id and redis_manager.task_exists(task_id):
                valid_tasks.append(task)
            else:
                print(f"⚠️  任务 {task_id} 已不存在，已过滤")
        
        return jsonify({
            'success': True,
            'tasks': valid_tasks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        print("=" * 60)
        print("📝 开始创建下载任务")
        print("=" * 60)
        
        data = request.get_json()
        url = data.get('url')
        
        print(f"📥 收到URL: {url}")
        
        if not url:
            print("❌ 错误：未提供视频链接")
            return jsonify({
                'success': False,
                'message': '请提供视频链接'
            }), 400
        
        task_id = str(uuid.uuid4())
        print(f"🆔 生成任务ID: {task_id}")
        
        # 检测平台
        print(f"🔍 检测视频平台...")
        if 'douyin.com' in url or 'v.douyin.com' in url:
            platform = 'douyin'
        elif 'bilibili.com' in url:
            platform = 'bilibili'
        elif 'toutiao.com' in url:
            platform = 'toutiao'
        else:
            platform = 'unknown'
        print(f"✅ 平台检测完成: {platform}")
        
        # 抖音平台特殊处理：跳过parser，直接创建任务
        if platform == 'douyin':
            print(f"📱 检测到抖音平台，跳过parser，直接创建任务")
            task_data = {
                'id': task_id,
                'url': url,
                'title': '抖音视频',
                'platform': 'douyin',
                'video_type': '短视频',
                'status': 'pending',
                'progress': 0,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"💾 保存任务到Redis...")
            redis_manager.set_task(task_id, task_data)
            print(f"✅ 任务已保存到Redis")
            
            print(f"📤 添加任务到下载队列...")
            redis_manager.add_task_to_queue(task_data)
            print(f"✅ 任务已添加到队列")
            
            print("=" * 60)
            print(f"✅ 任务创建成功")
            print("=" * 60)
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': '任务已添加到队列'
            })
        
        # 其他平台使用parser解析视频信息
        print(f"🔍 开始解析视频信息...")
        try:
            video_info = video_parser.parse_video_info(url)
            print(f"✅ 视频信息解析成功")
            print(f"   标题: {video_info.get('title', 'N/A')}")
            print(f"   平台: {video_info.get('platform', 'N/A')}")
            print(f"   类型: {video_info.get('video_type', 'N/A')}")
        except Exception as parse_error:
            print(f"❌ 错误：视频信息解析失败")
            print(f"   错误详情: {str(parse_error)}")
            print(f"   错误类型: {type(parse_error).__name__}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'视频信息解析失败: {str(parse_error)}',
                'error_details': {
                    'error_type': type(parse_error).__name__,
                    'error_message': str(parse_error),
                    'platform': platform,
                    'url': url
                }
            }), 500
        
        print(f"💾 准备保存任务数据...")
        task_data = {
            'id': task_id,
            'url': url,
            'title': video_info['title'],
            'platform': video_info['platform'],
            'video_type': video_info['video_type'],
            'status': 'pending',
            'progress': 0,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"💾 保存任务到Redis...")
        redis_manager.set_task(task_id, task_data)
        print(f"✅ 任务已保存到Redis")
        
        print(f"📤 添加任务到下载队列...")
        redis_manager.add_task_to_queue(task_data)
        print(f"✅ 任务已添加到队列")
        
        print("=" * 60)
        print(f"✅ 任务创建成功")
        print("=" * 60)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已添加到队列'
        })
    except Exception as e:
        print("=" * 60)
        print(f"❌ 错误：创建任务失败")
        print(f"   错误阶段: 任务创建流程")
        print(f"   错误详情: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return jsonify({
            'success': False,
            'message': f'创建任务失败: {str(e)}'
        }), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = redis_manager.get_task(task_id)
        if task:
            return jsonify({
                'success': True,
                'task': task
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/pause', methods=['POST'])
def pause_task(task_id):
    try:
        redis_manager.update_task_status(task_id, 'paused')
        return jsonify({
            'success': True,
            'message': '任务已暂停'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    try:
        redis_manager.update_task_status(task_id, 'cancelled')
        return jsonify({
            'success': True,
            'message': '任务已取消'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/retry', methods=['POST'])
def retry_task(task_id):
    try:
        redis_manager.update_task_status(task_id, 'pending', clear_error=True)
        redis_manager.add_task_to_queue(redis_manager.get_task(task_id))
        return jsonify({
            'success': True,
            'message': '任务已重新加入队列'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/open', methods=['POST'])
def open_task(task_id):
    try:
        print(f'Opening task: {task_id}')
        task = redis_manager.get_task(task_id)
        print(f'Task data: {task}')
        if task:
            save_path = task.get('save_path')
            print(f'Save path: {save_path}')
            if save_path and os.path.exists(save_path):
                print(f'File exists, opening: {save_path}')
                return jsonify({
                    'success': True,
                    'path': save_path
                })
            else:
                print(f'File does not exist or save_path is empty')
                return jsonify({
                    'success': False,
                    'message': '文件不存在'
                })
        else:
            print(f'Task not found')
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        print(f'Error opening task: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    try:
        logs = redis_manager.get_task_logs(task_id)
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task = redis_manager.get_task(task_id)
        if task:
            save_path = task.get('save_path')
            if save_path and os.path.exists(save_path):
                os.remove(save_path)
            
            redis_manager.delete_task(task_id)
            
            return jsonify({
                'success': True,
                'message': '任务已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/videos', methods=['GET'])
def get_videos():
    try:
        videos = redis_manager.get_all_videos()
        return jsonify({
            'success': True,
            'videos': videos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/videos/scan', methods=['POST'])
def scan_videos():
    try:
        storage_path = storage_manager.get_storage_path()
        
        if not os.path.exists(storage_path):
            return jsonify({
                'success': False,
                'message': '存储目录不存在'
            }), 404
        
        scanned_videos = []
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.m4v']
        
        for root, dirs, files in os.walk(storage_path):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in video_extensions:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    relative_path = os.path.relpath(file_path, storage_path)
                    path_parts = relative_path.split(os.sep)
                    
                    if len(path_parts) >= 2:
                        platform = path_parts[0]
                        title = path_parts[1]
                    else:
                        platform = 'unknown'
                        title = os.path.splitext(file)[0]
                    
                    video_id = str(uuid.uuid4())
                    video_data = {
                        'id': video_id,
                        'task_id': '',
                        'title': title,
                        'url': '',
                        'platform': platform,
                        'video_type': '短视频',
                        'save_path': file_path,
                        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    redis_manager.set_video(video_id, video_data)
                    scanned_videos.append(video_data)
        
        return jsonify({
            'success': True,
            'message': f'扫描完成，共发现 {len(scanned_videos)} 个视频文件',
            'videos': scanned_videos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/videos/search', methods=['GET'])
def search_videos():
    try:
        query = request.args.get('q', '')
        videos = redis_manager.get_all_videos()
        
        if query:
            filtered_videos = []
            for video in videos:
                title = video.get('title', '').lower()
                save_path = video.get('save_path', '').lower()
                
                if query.lower() in title or query.lower() in save_path:
                    filtered_videos.append(video)
            
            return jsonify({
                'success': True,
                'videos': filtered_videos
            })
        else:
            return jsonify({
                'success': True,
                'videos': videos
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/videos/delete', methods=['POST'])
def delete_video():
    try:
        data = request.get_json()
        path = data.get('path')
        is_folder = data.get('is_folder', False)
        
        if not path:
            return jsonify({
                'success': False,
                'message': '请提供路径'
            }), 400
        
        if not os.path.exists(path):
            return jsonify({
                'success': False,
                'message': '文件或目录不存在'
            }), 404
        
        if is_folder:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                
                deleted_videos = []
                videos = redis_manager.get_all_videos()
                for video in videos:
                    video_path = video.get('save_path', '')
                    if video_path and video_path.startswith(path):
                        redis_manager.redis_client.delete(f"video:{video.get('id')}")
                        deleted_videos.append(video.get('title'))
                
                return jsonify({
                    'success': True,
                    'message': f'已删除文件夹及其内容，共删除 {len(deleted_videos)} 个视频记录'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '路径不是目录'
                }), 400
        else:
            if os.path.isfile(path):
                os.remove(path)
                
                videos = redis_manager.get_all_videos()
                for video in videos:
                    if video.get('save_path') == path:
                        redis_manager.redis_client.delete(f"video:{video.get('id')}")
                        return jsonify({
                            'success': True,
                            'message': f'已删除视频：{video.get("title")}'
                        })
                
                return jsonify({
                    'success': True,
                    'message': '已删除文件'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '路径不是文件'
                }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/info', methods=['GET'])
def get_storage_info():
    try:
        info = storage_manager.get_storage_info()
        return jsonify({
            'success': True,
            'info': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/path', methods=['GET'])
def get_storage_path():
    try:
        path = storage_manager.get_storage_path()
        return jsonify({
            'success': True,
            'storage_path': path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/select-directory', methods=['POST'])
def select_storage_directory():
    try:
        data = request.get_json()
        platform = data.get('platform', 'macos')
        
        selected_path = storage_manager.select_storage_directory()
        
        if selected_path:
            return jsonify({
                'success': True,
                'selected_path': selected_path,
                'current_path': storage_manager.get_storage_path()
            })
        else:
            return jsonify({
                'success': False,
                'message': '未选择目录'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/migrate', methods=['POST'])
def migrate_storage():
    try:
        data = request.get_json()
        new_path = data.get('new_path')
        migrate_files = data.get('migrate_files', True)
        
        if not new_path:
            return jsonify({
                'success': False,
                'message': '请提供新路径'
            }), 400
        
        result = storage_manager.migrate_storage(new_path, migrate_files)
        
        return jsonify({
            'success': result['failed'] == 0,
            'message': result['message'] if result['failed'] > 0 else '迁移完成',
            'total': result['total'],
            'success': result['success'],
            'failed': result['failed']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/migration-status', methods=['GET'])
def get_migration_status():
    try:
        status = storage_manager.check_migration_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/cancel-migration', methods=['POST'])
def cancel_migration():
    try:
        result = storage_manager.cancel_migration()
        return jsonify({
            'success': True,
            'message': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/open-directory', methods=['POST'])
def open_directory():
    try:
        data = request.get_json()
        path = data.get('path')
        platform = data.get('platform', 'macos')
        
        if not path:
            return jsonify({
                'success': False,
                'message': '请提供路径'
            }), 400
        
        if platform == 'macos':
            import subprocess
            if path.endswith('.mp4') or path.endswith('.m4v') or path.endswith('.mov'):
                result = subprocess.run([
                    'open', 
                    '-a', 
                    'QuickTime Player',
                    path
                ], capture_output=True, text=True)
            else:
                result = subprocess.run(['open', path], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f'Failed to open file: {result.stderr}')
        elif platform == 'windows':
            import os
            os.startfile(path)
        else:
            import os
            os.startfile(path)
        
        return jsonify({
            'success': True,
            'message': '已打开目录'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/storage/move', methods=['POST'])
def move_file():
    try:
        data = request.get_json()
        source_path = data.get('source')
        target_path = data.get('target')
        
        if not source_path or not target_path:
            return jsonify({
                'success': False,
                'message': '请提供源路径和目标路径'
            }), 400
        
        import shutil
        shutil.move(source_path, target_path)
        
        return jsonify({
            'success': True,
            'message': '文件移动成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/auth/status', methods=['GET'])
def get_auth_status():
    try:
        status = platform_auth.get_platform_login_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/auth/login/<platform>', methods=['POST'])
def login_platform(platform):
    try:
        data = request.get_json()
        login_type = data.get('login_type', 'auto')
        
        if login_type == 'manual':
            cookie_string = data.get('cookie_string')
            
            if not cookie_string:
                return jsonify({
                    'success': False,
                    'message': '请提供Cookie字符串'
                }), 400
            
            if platform == 'bilibili':
                success, message = platform_auth.login_bilibili_manual(cookie_string)
            elif platform == 'douyin':
                success, message = platform_auth.login_douyin_manual(cookie_string)
            elif platform == 'toutiao':
                success, message = platform_auth.login_toutiao_manual(cookie_string)
            else:
                return jsonify({
                    'success': False,
                    'message': '不支持的平台'
                }), 400
        else:
            if platform == 'bilibili':
                success, message = platform_auth.login_bilibili('', '')
            elif platform == 'douyin':
                success, message = platform_auth.login_douyin('', '')
            elif platform == 'toutiao':
                success, message = platform_auth.login_toutiao('', '')
            else:
                return jsonify({
                    'success': False,
                    'message': '不支持的平台'
                }), 400
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def process_download_queue():
    while True:
        task_data = redis_manager.get_next_task()
        if task_data:
            task_id = task_data.get('id')
            storage_path = storage_manager.get_storage_path()
            
            success, message = video_downloader.download_video(
                task_data.get('url'),
                task_id,
                storage_path
            )
            
            if success:
                task = redis_manager.get_task(task_id)
                downloaded_path = task.get('save_path')
                
                if not downloaded_path or not os.path.exists(downloaded_path):
                    redis_manager.update_task_status(task_id, 'failed')
                    continue
                
                video_info = video_parser.parse_video_info(task_data.get('url'))
                video_path = os.path.join(
                    storage_path,
                    video_info['platform'],
                    video_info['title'],
                    f"{video_info['title']}.{Config.OUTPUT_FORMAT}"
                )
                
                transcode_success, transcode_message = video_transcoder.transcode_video(
                    downloaded_path,
                    video_path,
                    task_id
                )
                
                if transcode_success:
                    video_data = {
                        'id': str(uuid.uuid4()),
                        'task_id': task_id,
                        'title': video_info['title'],
                        'url': task_data.get('url'),
                        'platform': video_info['platform'],
                        'video_type': video_info['video_type'],
                        'save_path': video_path,
                        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    redis_manager.set_video(video_data['id'], video_data)
                    redis_manager.update_task_status(task_id, 'completed', progress=100, save_path=video_path)
                else:
                    if os.path.exists(downloaded_path):
                        video_data = {
                            'id': str(uuid.uuid4()),
                            'task_id': task_id,
                            'title': video_info['title'],
                            'url': task_data.get('url'),
                            'platform': video_info['platform'],
                            'video_type': video_info['video_type'],
                            'save_path': downloaded_path,
                            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        redis_manager.set_video(video_data['id'], video_data)
                        redis_manager.update_task_status(task_id, 'completed', progress=100, save_path=downloaded_path)
                    else:
                        redis_manager.update_task_status(task_id, 'failed')
            else:
                redis_manager.update_task_status(task_id, 'failed')
        else:
            time.sleep(1)

if __name__ == '__main__':
    import logging
    import os
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print('\n🚀 启动自动下载视频应用...')
        print('=' * 60)
        print(f'📡 服务器地址: http://192.168.31.226:5001')
        print('💡 按 Ctrl+C 停止服务器')
        print('=' * 60)
        print()
    
    download_thread = threading.Thread(target=process_download_queue, daemon=True)
    download_thread.start()
    
    app.run(host='192.168.31.226', port=5001, debug=Config.DEBUG)