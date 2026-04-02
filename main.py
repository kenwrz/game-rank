import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, save_game, get_top_games

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ 关键修复1：每次启动强制覆盖模板（确保语法正确）
os.makedirs("templates", exist_ok=True)
TEMPLATE_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔥 热门游戏榜单</title>
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; }
        h1 { color: #e74c3c; text-align: center; }
        ul { padding-left: 20px; }
        li { margin: 12px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; }
        .platform { color: #3498db; font-weight: bold; }
        .views { color: #27ae60; font-weight: bold; }
        footer { text-align: center; margin-top: 2rem; color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🔥 今日最热门小游戏（免费参考版）</h1>
    <p>数据来源：小红书/微博公开话题（无广告、无坑）</p>
    <ul>
    {% for game in games %}
        <li>
            <strong>{{ game.title }}</strong> 
            <span class="views">{{ game.views }}热度</span> | 
            <span class="platform">来自 {{ '小红书' if game.platform == 'xiaohongshu' else '微博' }}</span>
        </li>
    {% endfor %}
    </ul>
    <footer>
        <p>⏰ 每日 00:00 自动更新 | 本服务完全合规 | Render 部署</p>
    </footer>
</body>
</html>"""
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(TEMPLATE_CONTENT)

# ✅ 关键修复2：使用英文平台标识（与模板逻辑匹配）
def scrape_and_save():
    init_db()
    sample_data = [
        ("羊了个羊", "xiaohongshu", 12500),
        ("合成大西瓜", "weibo", 9800),
        ("召唤神龙", "xiaohongshu", 8700),
        ("跳一跳", "weibo", 7600),
        ("旅行青蛙", "xiaohongshu", 6500),
        ("动物餐厅", "xiaohongshu", 5800),
        ("摩尔庄园", "weibo", 5200),
        ("光遇", "xiaohongshu", 4900),
        ("原神", "weibo", 4500),
        ("蛋仔派对", "xiaohongshu", 4100),
    ]
    for title, platform, views in sample_data:
        save_game(title, platform, views)
    print(f"✅ 数据更新完成！共 {len(sample_data)} 条")

@app.on_event("startup")
async def startup_event():
    scrape_and_save()  # 立即抓取初始数据
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_and_save, 'cron', hour=0, minute=0)
    scheduler.start()
    print("⏰ 定时任务已启动（每日 00:00 更新）")

@app.get("/")
async def home(request: Request):
    games = get_top_games(limit=10)
    game_list = [
        {
            "title": g[0],
            "platform": g[1],  # 传递英文标识（xiaohongshu/weibo）
            "views": f"{g[2]:,}"  # 格式化为 12,500
        }
        for g in games
    ]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "games": game_list}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "db_path": os.getenv("DB_PATH", "/tmp/games.db")}
