import os
import shutil
import platform
import subprocess
from redis_manager import RedisManager
from config import Config

class StorageManager:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.current_os = platform.system()
    
    def get_storage_path(self):
        return self.redis.get_storage_path() or Config.DEFAULT_STORAGE_PATH
    
    def set_storage_path(self, new_path):
        if not os.path.exists(new_path):
            raise Exception(f'目录不存在: {new_path}')
        
        if not os.path.isdir(new_path):
            raise Exception(f'路径不是目录: {new_path}')
        
        return self.redis.set_storage_path(new_path)
    
    def select_storage_directory(self):
        if self.current_os == 'Darwin':
            return self._select_directory_macos()
        elif self.current_os == 'Windows':
            return self._select_directory_windows()
        else:
            return self._select_directory_linux()
    
    def _select_directory_macos(self):
        try:
            script = '''
            tell application "Finder" to activate
            set newFolder to POSIX path of (choose folder with prompt "选择存储目录" default location POSIX path of (path to home folder))
            return newFolder as text
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                selected_path = result.stdout.strip()
                if selected_path and os.path.isdir(selected_path):
                    return selected_path
            return None
            
        except Exception as e:
            return None
    
    def _select_directory_windows(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            
            selected_path = filedialog.askdirectory(
                title='选择存储目录',
                initialdir=os.path.expanduser('~')
            )
            
            if selected_path and os.path.isdir(selected_path):
                return selected_path
            return None
            
        except Exception as e:
            return None
    
    def _select_directory_linux(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            
            selected_path = filedialog.askdirectory(
                title='选择存储目录',
                initialdir=os.path.expanduser('~')
            )
            
            if selected_path and os.path.isdir(selected_path):
                return selected_path
            return None
            
        except Exception as e:
            return None
    
    def migrate_storage(self, new_path, migrate_files=True):
        old_path = self.get_storage_path()
        
        if not os.path.exists(old_path):
            raise Exception(f'原存储目录不存在: {old_path}')
        
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
        
        self.redis.set_old_storage_path(old_path)
        self.redis.set_migration_status('in_progress')
        self.redis.set_migration_progress(0)
        
        try:
            if migrate_files:
                result = self._migrate_files(old_path, new_path)
            else:
                result = {'total': 0, 'success': 0, 'failed': 0, 'failed_files': []}
            
            if result['failed'] == 0:
                self.redis.set_storage_path(new_path)
                self.redis.set_migration_status('completed')
                self.redis.set_migration_progress(100)
                return True, f'迁移完成: {result["success"]}个文件'
            else:
                self.redis.set_migration_status('failed')
                return False, f'迁移失败: {result["failed"]}个文件失败'
                
        except Exception as e:
            self.redis.set_migration_status('failed')
            return False, f'迁移异常: {str(e)}'
    
    def _migrate_files(self, old_path, new_path):
        total_files = 0
        success_count = 0
        failed_files = []
        
        for root, dirs, files in os.walk(old_path):
            for file in files:
                total_files += 1
                
                src_file = os.path.join(root, file)
                dst_file = os.path.join(new_path, os.path.relpath(root, old_path), file)
                
                dst_dir = os.path.dirname(dst_file)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir, exist_ok=True)
                
                try:
                    shutil.copy2(src_file, dst_file)
                    success_count += 1
                    
                    progress = int((success_count / total_files) * 100)
                    self.redis.set_migration_progress(progress)
                    
                except Exception as e:
                    failed_files.append({
                        'file': src_file,
                        'error': str(e)
                    })
        
        return {
            'total': total_files,
            'success': success_count,
            'failed': len(failed_files),
            'failed_files': failed_files
        }
    
    def check_migration_status(self):
        status = self.redis.get_migration_status()
        
        if status == 'in_progress':
            old_path = self.redis.get_old_storage_path()
            new_path = self.get_storage_path()
            
            if old_path and new_path and old_path != new_path:
                return {
                    'status': 'in_progress',
                    'message': '检测到未完成的迁移，是否继续？',
                    'old_path': old_path,
                    'new_path': new_path
                }
        
        return {
            'status': 'none',
            'message': '没有未完成的迁移'
        }
    
    def continue_migration(self):
        old_path = self.redis.get_old_storage_path()
        new_path = self.get_storage_path()
        
        if not old_path or not new_path:
            return False, '无法继续迁移：路径信息不完整'
        
        try:
            result = self._migrate_files(old_path, new_path)
            
            if result['failed'] == 0:
                self.redis.set_storage_path(new_path)
                self.redis.set_migration_status('completed')
                self.redis.set_migration_progress(100)
                return True, f'迁移完成: {result["success"]}个文件'
            else:
                return False, f'迁移失败: {result["failed"]}个文件失败'
                
        except Exception as e:
            return False, f'迁移异常: {str(e)}'
    
    def cancel_migration(self):
        self.redis.set_migration_status('cancelled')
        self.redis.set_migration_progress(0)
        return True, '已取消迁移'
    
    def get_storage_info(self):
        storage_path = self.get_storage_path()
        
        if not os.path.exists(storage_path):
            return {
                'path': storage_path,
                'exists': False,
                'size': 0,
                'file_count': 0
            }
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(storage_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_count += 1
                except Exception:
                    pass
        
        return {
            'path': storage_path,
            'exists': True,
            'size': total_size,
            'file_count': file_count
        }
    
    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} PB'