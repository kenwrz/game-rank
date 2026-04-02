import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/tmp/games.db")

def get_connection():
    """获取数据库连接（自动创建目录）"""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """初始化数据库（安全创建表）"""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform TEXT NOT NULL,
                views INTEGER NOT NULL
            )
        """)
        # 清空旧数据（确保每日更新干净）
        c.execute("DELETE FROM games")
        conn.commit()
    finally:
        conn.close()

def save_game(title, platform, views):
    """保存单条游戏数据"""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO games (title, platform, views) VALUES (?, ?, ?)",
            (title, platform, views)
        )
        conn.commit()
    finally:
        conn.close()

def get_top_games(limit=10):
    """获取热门游戏（按热度排序）"""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT title, platform, views 
            FROM games 
            ORDER BY views DESC 
            LIMIT ?
        """, (limit,))
        return c.fetchall()
    finally:
        conn.close()
