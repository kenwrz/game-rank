import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, save_game, get_top_games

# 初始化应用
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 创建 templates 目录和基础模板（避免模板缺失错误）
os.makedirs("templates", exist_ok=True)
if not os.path.exists("templates/index.html"):
    with open("templates/index.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head><title>热门游戏榜单</title></head>
<body>
<h1>🔥 今日最热门小游戏（免费参考版）</h1>
<p>数据来源：小红书/微博公开话题（无广告、无坑）</p>
<ul>
{% for game in games %}
  <li>[{{ game.title }}] {{ game.views }}热度 | 来自{{ game.platform }}</li>
{% endfor %}
</ul>
<p><small>每日00:00自动更新 | 本服务完全合规</small></p>
</body>
</html>
        """)

# 模拟抓取函数（替换为您的实际逻辑）
def scrape_and_save():
    init_db()  # 确保表存在且清空旧数据
    # 示例数据（替换为您的爬虫逻辑）
    sample_data = [
        ("羊了个羊", "小红书", 12500),
        ("合成大西瓜", "微博", 9800),
        ("召唤神龙", "小红书", 8700),
        ("跳一跳", "微博", 7600),
        ("旅行青蛙", "小红书", 6500),
    ]
    for title, platform, views in sample_data:
        save_game(title, platform, views)
    print("✅ 数据更新完成！共", len(sample_data), "条")

# 应用启动时初始化
@app.on_event("startup")
async def startup_event():
    scrape_and_save()  # 立即抓取初始数据
    # 设置每日00:00自动更新
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_and_save, 'cron', hour=0, minute=0)
    scheduler.start()
    print("⏰ 定时任务已启动（每日00:00更新）")

# 首页路由
@app.get("/")
async def home(request: Request):
    games = get_top_games(limit=10)
    # 转换为模板友好的格式
    game_list = [
        {"title": g[0], "platform": g[1], "views": f"{g[2]:,}"}
        for g in games
    ]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "games": game_list}
    )

# 健康检查端点（Render 需要）
@app.get("/health")
async def health_check():
    return {"status": "ok", "db_path": os.getenv("DB_PATH", "/tmp/games.db")}
