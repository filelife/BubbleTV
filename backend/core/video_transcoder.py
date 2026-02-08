import subprocess
import os
from core.redis_manager import RedisManager
from config.config import Config

class VideoTranscoder:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.ffmpeg_path = Config.FFMPEG_PATH
        self.output_format = Config.OUTPUT_FORMAT
    
    def _log(self, task_id, message):
        """记录任务日志"""
        if task_id:
            self.redis.add_task_log(task_id, message)
            print(f"[{task_id[:8]}] {message}")
        else:
            print(f"[LOG] {message}")
    
    def check_ffmpeg_installed(self):
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            return False
    
    def transcode_video(self, input_file, output_file, task_id=None):
        self._log(task_id, "========== 开始视频转码 ==========")
        self._log(task_id, f"输入文件: {input_file}")
        self._log(task_id, f"输出文件: {output_file}")
        
        if not self.check_ffmpeg_installed():
            self._log(task_id, "❌ FFmpeg未安装")
            raise Exception('FFmpeg未安装，无法进行视频转码')
        
        if not os.path.exists(input_file):
            self._log(task_id, f"❌ 输入文件不存在: {input_file}")
            raise Exception(f'输入文件不存在: {input_file}')
        
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            self._log(task_id, f"✅ 创建输出目录: {output_dir}")
        
        try:
            # 获取视频时长
            self._log(task_id, "📊 获取视频时长...")
            duration = self._get_video_duration(input_file)
            if duration <= 0:
                duration = 3600  # 默认1小时
                self._log(task_id, "⚠️  无法获取视频时长，使用默认值3600秒")
            else:
                self._log(task_id, f"✅ 视频时长: {duration}秒 ({duration/60:.2f}分钟)")
            
            self._log(task_id, "🎬 开始FFmpeg转码...")
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-f', 'mov',
                '-y',  # 覆盖输出文件
                output_file
            ]
            
            self._log(task_id, f"📋 FFmpeg命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # 行缓冲
            )
            
            if task_id:
                self._monitor_progress(process, task_id, duration)
            
            # 等待进程完成，设置超时
            try:
                return_code = process.wait(timeout=1800)  # 30分钟超时
                stdout, stderr = process.stdout.read(), process.stderr.read()
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.stdout.read(), process.stderr.read()
                self._log(task_id, "❌ 转码超时：超过30分钟未完成")
                return False, '转码超时：超过30分钟未完成'
            
            if return_code == 0:
                self._log(task_id, "✅ 转码成功")
                return True, '转码成功'
            else:
                self._log(task_id, f"❌ 转码失败，返回码: {return_code}")
                self._log(task_id, f"📋 FFmpeg错误输出: {stderr[:500]}")
                return False, f'转码失败: {stderr}'
                
        except Exception as e:
            self._log(task_id, f"❌ 转码异常: {str(e)}")
            return False, f'转码异常: {str(e)}'
    
    def _get_video_duration(self, input_file):
        """获取视频时长（秒）"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-f', 'null',
                '-'
            ]
            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            # 从FFmpeg输出中解析时长
            import re
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', result.stderr)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                return hours * 3600 + minutes * 60 + seconds
            
            return 0
        except Exception as e:
            print(f'获取视频时长失败: {e}')
            return 0
    
    def _monitor_progress(self, process, task_id, duration):
        import re
        import threading
        import time
        progress_pattern = re.compile(r'time=(\d+):(\d+):(\d+)')
        
        def read_stderr():
            last_progress = 0
            line_count = 0
            self._log(task_id, "📡 开始监控FFmpeg输出...")
            
            while True:
                line = process.stderr.readline()
                if not line:
                    self._log(task_id, "📡 FFmpeg输出结束")
                    break
                
                line_count += 1
                
                # 每100行记录一次，避免日志过多
                if line_count % 100 == 0:
                    self._log(task_id, f"📡 已读取 {line_count} 行FFmpeg输出")
                
                match = progress_pattern.search(line)
                if match:
                    try:
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        seconds = int(match.group(3))
                        
                        # 转换为总秒数
                        time_current = hours * 3600 + minutes * 60 + seconds
                        
                        # 使用实际视频时长
                        time_total = duration
                        
                        # 防止除零错误
                        if time_total > 0:
                            progress = int((time_current / time_total) * 100)
                        else:
                            progress = 0
                        
                        # 限制进度在0-100之间
                        progress = max(0, min(100, progress))
                        
                        # 只记录有变化的进度
                        if progress != last_progress:
                            self.redis.update_task_status(task_id, 'transcoding', progress=progress)
                            self._log(task_id, f"📊 转码进度: {progress}% (时间: {time_current}/{time_total}秒)")
                            last_progress = progress
                    except Exception as e:
                        self._log(task_id, f"Error parsing progress: {e}")
                        pass
                
                # 检查进程是否还在运行
                if process.poll() is not None:
                    self._log(task_id, f"📡 FFmpeg进程已结束，退出码: {process.returncode}")
                    break
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.1)
            
            self._log(task_id, f"📡 监控线程结束，共读取 {line_count} 行")
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=read_stderr, daemon=True)
        monitor_thread.start()
        self._log(task_id, "✅ 监控线程已启动")
    
    def batch_transcode(self, input_files, output_dir, task_id=None):
        success_count = 0
        failed_files = []
        
        for i, input_file in enumerate(input_files):
            if not input_file.endswith(('.mp4', '.avi', '.mkv', '.flv')):
                continue
            
            filename = os.path.basename(input_file)
            output_file = os.path.join(output_dir, f'{os.path.splitext(filename)[0]}.{self.output_format}')
            
            success, message = self.transcode_video(input_file, output_file, task_id)
            
            if success:
                success_count += 1
            else:
                failed_files.append({
                    'file': input_file,
                    'error': message
                })
            
            if task_id:
                # 防止除零错误
                if len(input_files) > 0:
                    progress = int(((i + 1) / len(input_files)) * 100)
                else:
                    progress = 100
                self.redis.update_task_status(task_id, 'transcoding', progress=progress)
        
        return {
            'total': len(input_files),
            'success': success_count,
            'failed': len(failed_files),
            'failed_files': failed_files
        }
    
    def get_video_info(self, video_file):
        cmd = [
            self.ffmpeg_path,
            '-i', video_file,
            '-f', 'null'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                return {
                    'duration': total_seconds,
                    'format': 'unknown'
                }
            
            return None
            
        except Exception as e:
            return None