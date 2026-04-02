import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def scrape_xiaohongshu():
    """爬取小红书小程序游戏热门笔记"""
    url = "https://www.xiaohongshu.com/search?keyword=小程序游戏"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取笔记标题和阅读量（示例，实际需根据页面结构调整）
        games = []
        for item in soup.select('.note-item'):
            title_tag = item.select_one('.title')
            views_tag = item.select_one('.view-count')
            
            if title_tag and views_tag:
                title = title_tag.text.strip()
                # 提取数字（如"1.2万" → 12000）
                views = re.sub(r'[^\d.]', '', views_tag.text)
                views = int(float(views)) if '.' in views else int(views)
                games.append((title, views))
        
        return games
    except Exception as e:
        print(f"小红书爬取失败: {e}")
        return []

def scrape_weibo():
    """爬取微博#微信小游戏#话题热门微博"""
    url = "https://s.weibo.com/weibo?q=%23微信小游戏%23"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        games = []
        for item in soup.select('.card-wrap'):
            title_tag = item.select_one('.title')
            stats_tag = item.select_one('.stat')
            
            if title_tag and stats_tag:
                title = title_tag.text.strip()
                # 提取转发/点赞数（示例）
                stats = stats_tag.text.replace('转发', '').replace('评论', '').strip()
                views = int(re.sub(r'[^\d]', '', stats))
                games.append((title, views))
        
        return games
    except Exception as e:
        print(f"微博爬取失败: {e}")
        return []