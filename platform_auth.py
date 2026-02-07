from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pickle
import os
from redis_manager import RedisManager
from config import Config

class PlatformAuth:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.driver = None
    
    def login_bilibili(self, username, password):
        try:
            chrome_options = Options()
            if Config.BROWSER_HEADLESS:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.get('https://passport.bilibili.com/login')
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            
            username_input = self.driver.find_element(By.ID, 'username')
            password_input = self.driver.find_element(By.ID, 'password')
            login_button = self.driver.find_element(By.CLASS_NAME, 'btn-login')
            
            username_input.send_keys(username)
            password_input.send_keys(password)
            login_button.click()
            
            time.sleep(3)
            
            cookies = self.driver.get_cookies()
            
            cookie_data = {}
            for cookie in cookies:
                cookie_data[cookie['name']] = cookie['value']
            
            self.redis.set_cookie('bilibili', cookie_data)
            
            self.driver.quit()
            
            return True, 'Bilibili登录成功'
            
        except Exception as e:
            if self.driver:
                self.driver.quit()
            return False, f'Bilibili登录失败: {str(e)}'
    
    def login_douyin(self, username, password):
        try:
            chrome_options = Options()
            if Config.BROWSER_HEADLESS:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.get('https://www.douyin.com/passport/web/login')
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'login-btn'))
            )
            
            cookies = self.driver.get_cookies()
            
            cookie_data = {}
            for cookie in cookies:
                cookie_data[cookie['name']] = cookie['value']
            
            self.redis.set_cookie('douyin', cookie_data)
            
            self.driver.quit()
            
            return True, '抖音登录成功'
            
        except Exception as e:
            if self.driver:
                self.driver.quit()
            return False, f'抖音登录失败: {str(e)}'
    
    def login_toutiao(self, username, password):
        try:
            chrome_options = Options()
            if Config.BROWSER_HEADLESS:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.get('https://sso.toutiao.com/auth/')
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'login-btn'))
            )
            
            cookies = self.driver.get_cookies()
            
            cookie_data = {}
            for cookie in cookies:
                cookie_data[cookie['name']] = cookie['value']
            
            self.redis.set_cookie('toutiao', cookie_data)
            
            self.driver.quit()
            
            return True, '今日头条登录成功'
            
        except Exception as e:
            if self.driver:
                self.driver.quit()
            return False, f'今日头条登录失败: {str(e)}'
    
    def check_cookie_validity(self, platform):
        if not self.redis.is_cookie_valid(platform):
            return False, 'Cookie不存在或已过期'
        return True, 'Cookie有效'
    
    def get_platform_login_status(self):
        platforms = ['bilibili', 'douyin', 'toutiao']
        status = {}
        
        for platform in platforms:
            is_valid = self.redis.is_cookie_valid(platform)
            status[platform] = {
                'logged_in': is_valid,
                'status': '已登录' if is_valid else '未登录'
            }
        
        return status