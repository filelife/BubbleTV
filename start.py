#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import socket
import signal

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    try:
        if sys.platform == 'darwin':
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    os.kill(int(pid), signal.SIGTERM)
                print(f'已关闭端口 {port} 上的进程')
        elif sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], 
                                capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid], 
                                     capture_output=True)
                        print(f'已关闭端口 {port} 上的进程')
    except Exception as e:
        print(f'关闭进程时出错: {e}')

def main():
    HOST = '192.168.31.226'
    PORT = 5001
    
    print('🚀 启动自动下载视频应用...')
    print('=' * 60)
    
    if is_port_in_use(PORT):
        print(f'⚠️  端口 {PORT} 已被占用')
        choice = input('是否关闭占用端口的进程并重新启动？(y/n): ')
        if choice.lower() == 'y':
            kill_process_on_port(PORT)
            time.sleep(1)
        else:
            print('❌ 启动取消')
            sys.exit(1)
    
    print(f'📡 服务器地址: http://{HOST}:{PORT}')
    print('💡 按 Ctrl+C 停止服务器')
    print('=' * 60)
    
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print('\n\n👋 服务器已停止')
    except Exception as e:
        print(f'\n❌ 启动失败: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()