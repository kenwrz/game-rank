from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from database import init_db, save_game
from scraper import scrape_xiaohongshu, scrape_weibo
from apscheduler.schedulers.background import BackgroundScheduler
import datetime,os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
init_db()

def update_data():
    """每日更新数据（00:00执行）"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 爬取小红书
    xiaohongshu_games = scrape_xiaohongshu()
    for title, views in xiaohongshu_games:
        save_game(title, "xiaohongshu", views, today)
    
    # 爬取微博
    weibo_games = scrape_weibo()
    for title, views in weibo_games:
        save_game(title, "weibo", views, today)
    
    print(f"✅ {today} 数据更新完成")

# 启动定时任务（每日0点）
scheduler = BackgroundScheduler()
scheduler.add_job(update_data, 'cron', hour=0)
scheduler.start()

@app.get("/")
async def home(request: Request):
    """主页：展示最新热门游戏"""
    conn = sqlite3.connect(os.getenv("DB_PATH", ":memory:"))
    c = conn.cursor()
    
    # 获取最新数据（按热度排序）
    c.execute("""
        SELECT title, platform, views 
        FROM games 
        WHERE date = (SELECT MAX(date) FROM games)
        ORDER BY views DESC
        LIMIT 10
    """)
    
    games = [{"title": row[0], "platform": row[1], "views": row[2]} for row in c.fetchall()]
    conn.close()
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "games": games}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
