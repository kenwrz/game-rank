import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", ":memory:")#":memory:"

def init_db():
    """初始化数据库（自动创建表）"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 关键修复：添加 IF NOT EXISTS
    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            platform TEXT,
            views INTEGER
        )
    """)
        conn.commit()
        conn.close()

def save_game(title, platform, views, date):
    """保存游戏数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO games (title, platform, views, date)
        VALUES (?, ?, ?, ?)
    """, (title, platform, views, date))
    conn.commit()
    conn.close()
