import redis
import json
from datetime import datetime
from config import Config

class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def set_user(self, user_id, user_data):
        key = f'user:{user_id}'
        self.redis_client.hset(key, mapping=user_data)
        return True
    
    def get_user(self, user_id):
        key = f'user:{user_id}'
        return self.redis_client.hgetall(key)
    
    def set_task(self, task_id, task_data):
        key = f'task:{task_id}'
        self.redis_client.hset(key, mapping=task_data)
        return True
    
    def get_task(self, task_id):
        key = f'task:{task_id}'
        return self.redis_client.hgetall(key)
    
    def update_task_status(self, task_id, status, progress=None):
        key = f'task:{task_id}'
        self.redis_client.hset(key, 'status', status)
        self.redis_client.hset(key, 'updated_at', datetime.now().isoformat())
        if progress is not None:
            self.redis_client.hset(key, 'progress', str(progress))
    
    def set_video(self, video_id, video_data):
        key = f'video:{video_id}'
        self.redis_client.hset(key, mapping=video_data)
        return True
    
    def get_video(self, video_id):
        key = f'video:{video_id}'
        return self.redis_client.hgetall(key)
    
    def get_all_videos(self):
        pattern = 'video:*'
        keys = self.redis_client.keys(pattern)
        videos = []
        for key in keys:
            video_data = self.redis_client.hgetall(key)
            videos.append(video_data)
        return videos
    
    def set_config(self, config_key, config_value):
        key = f'config:{config_key}'
        self.redis_client.set(key, config_value)
        return True
    
    def get_config(self, config_key):
        key = f'config:{config_key}'
        return self.redis_client.get(key)
    
    def set_storage_path(self, storage_path):
        return self.set_config('storage_path', storage_path)
    
    def get_storage_path(self):
        return self.get_config('storage_path') or Config.DEFAULT_STORAGE_PATH
    
    def set_migration_status(self, status):
        return self.set_config('migration_status', status)
    
    def get_migration_status(self):
        return self.get_config('migration_status') or 'none'
    
    def set_old_storage_path(self, old_path):
        return self.set_config('old_storage_path', old_path)
    
    def get_old_storage_path(self):
        return self.get_config('old_storage_path')
    
    def set_migration_progress(self, progress):
        return self.set_config('migration_progress', str(progress))
    
    def get_migration_progress(self):
        progress = self.get_config('migration_progress')
        return int(progress) if progress else 0
    
    def set_cookie(self, platform, cookie_data):
        key = f'cookie:{platform}'
        self.redis_client.hset(key, mapping=cookie_data)
        self.redis_client.expire(key, Config.COOKIE_EXPIRY_DAYS * 24 * 60 * 60)
        return True
    
    def get_cookie(self, platform):
        key = f'cookie:{platform}'
        return self.redis_client.hgetall(key)
    
    def is_cookie_valid(self, platform):
        key = f'cookie:{platform}'
        return self.redis_client.exists(key)
    
    def add_task_to_queue(self, task_data):
        task_json = json.dumps(task_data)
        self.redis_client.lpush('download_queue', task_json)
        return True
    
    def get_next_task(self):
        task_json = self.redis_client.rpop('download_queue')
        if task_json:
            return json.loads(task_json)
        return None
    
    def get_all_tasks(self):
        pattern = 'task:*'
        keys = self.redis_client.keys(pattern)
        tasks = []
        for key in keys:
            task_data = self.redis_client.hgetall(key)
            tasks.append(task_data)
        return tasks
    
    def delete_task(self, task_id):
        key = f'task:{task_id}'
        return self.redis_client.delete(key)
    
    def close(self):
        self.redis_client.close()