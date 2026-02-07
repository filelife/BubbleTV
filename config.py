import os

class Config:
    DEBUG = True
    
    SECRET_KEY = 'your-secret-key-here'
    
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    
    DEFAULT_STORAGE_PATH = os.path.join(os.path.expanduser('~'), 'Downloads', 'Videos')
    
    MAX_DOWNLOAD_THREADS = 3
    DOWNLOAD_TIMEOUT = 300
    
    FFMPEG_PATH = 'ffmpeg'
    OUTPUT_FORMAT = 'mov'
    
    BROWSER_HEADLESS = True
    
    COOKIE_EXPIRY_DAYS = 30
    
    MIGRATION_CHECK_INTERVAL = 60