import subprocess
import os
from redis_manager import RedisManager
from config import Config

class VideoTranscoder:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.ffmpeg_path = Config.FFMPEG_PATH
        self.output_format = Config.OUTPUT_FORMAT
    
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
        if not self.check_ffmpeg_installed():
            raise Exception('FFmpeg未安装，无法进行视频转码')
        
        if not os.path.exists(input_file):
            raise Exception(f'输入文件不存在: {input_file}')
        
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_file
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            if task_id:
                self._monitor_progress(process, task_id)
            
            stdout, stderr = process.communicate()
            return_code = process.returncode
            
            if return_code == 0:
                return True, '转码成功'
            else:
                return False, f'转码失败: {stderr}'
                
        except Exception as e:
            return False, f'转码异常: {str(e)}'
    
    def _monitor_progress(self, process, task_id):
        import re
        progress_pattern = re.compile(r'time=(\d+):(\d+)')
        
        while True:
            line = process.stderr.readline()
            if not line:
                break
            
            match = progress_pattern.search(line)
            if match:
                time_total = int(match.group(1))
                time_current = int(match.group(2))
                progress = int((time_current / time_total) * 100)
                self.redis.update_task_status(task_id, 'transcoding', progress=progress)
    
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
                progress = int(((i + 1) / len(input_files)) * 100)
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