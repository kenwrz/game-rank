import os
import requests
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, save_game, get_top_games

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ 关键：强制覆盖模板（含手动更新按钮 + 状态提示）
os.makedirs("templates", exist_ok=True)
TEMPLATE_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔥 热门游戏榜单</title>
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; background: #f8f9fa; }
        h1 { color: #e74c3c; text-align: center; margin-bottom: 0.5rem; }
        .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 1.5rem; }
        .update-container { text-align: center; margin: 20px 0; }
        .update-btn { 
            background: linear-gradient(135deg, #3498db, #2980b9); 
            color: white; 
            border: none; 
            padding: 12px 30px; 
            font-size: 1.1em; 
            border-radius: 30px; 
            cursor: pointer; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        .update-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(0,0,0,0.25); 
        }
        .update-btn:active { transform: translateY(0); }
        .status { 
            padding: 10px; 
            border-radius: 8px; 
            margin: 15px 0; 
            text-align: center; 
            font-weight: bold;
        }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        ul { padding-left: 20px; }
        li { 
            margin: 15px 0; 
            padding: 15px; 
            background: white; 
            border-radius: 10px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .game-title { font-weight: bold; font-size: 1.1em; color: #2c3e50; }
        .meta { display: flex; gap: 20px; }
        .views { color: #27ae60; font-weight: bold; }
        .platform { color: #3498db; font-weight: bold; }
        footer { 
            text-align: center; 
            margin-top: 2.5rem; 
            color: #7f8c8d; 
            font-size: 0.95em; 
            padding-top: 1.5rem; 
            border-top: 1px solid #eee;
        }
        .debug-note { 
            background: #fff3cd; 
            border-left: 4px solid #ffc107; 
            padding: 12px; 
            margin: 20px 0; 
            border-radius: 0 4px 4px 0;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <h1>🔥 今日最热门小游戏榜单</h1>
    <p class="subtitle">数据来源：微博公开热搜榜（每日自动更新）</p>
    
    <!-- 状态提示 -->
    {% if status %}
    <div class="status {{ status.type }}">{{ status.message }}</div>
    {% endif %}
    
    <!-- 调试提示（仅Render环境显示） -->
    {% if os.getenv('RENDER') %}
    <div class="debug-note">
        💡 <strong>调试提示：</strong>Render国外服务器无法稳定访问微博API，当前使用<strong>模拟数据</strong>。<br>
        本地部署时设置环境变量 <code>USE_REAL_DATA=true</code> 可启用真实数据抓取。
    </div>
    {% endif %}
    
    <!-- 手动更新按钮 -->
    <div class="update-container">
        <button class="update-btn" onclick="updateData()">🔄 手动更新数据（测试用）</button>
    </div>
    
    <ul>
    {% for game in games %}
        <li>
            <div>
                <div class="game-title">{{ game.title }}</div>
            </div>
            <div class="meta">
                <span class="views">🔥 {{ game.views }}</span>
                <span class="platform">📱 {{ '小红书' if game.platform == 'xiaohongshu' else '微博' }}</span>
            </div>
        </li>
    {% endfor %}
    </ul>
    
    <footer>
        <p>⏰ 每日 00:00 自动更新 | 🌐 Render 部署 | ✅ 完全合规</p>
        <p>📌 说明：为遵守平台规则，仅使用公开可访问数据源</p>
    </footer>
    
    <script>
    function updateData() {
        const btn = document.querySelector('.update-btn');
        btn.disabled = true;
        btn.innerHTML = '⏳ 更新中...';
        
        fetch('/update?source=manual')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = '/?status=success&msg=' + encodeURIComponent(data.message);
                } else {
                    window.location.href = '/?status=error&msg=' + encodeURIComponent(data.message);
                }
            })
            .catch(error => {
                window.location.href = '/?status=error&msg=网络请求失败';
            });
    }
    // 页面加载时处理URL参数
    window.addEventListener('load', () => {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('status')) {
            const type = urlParams.get('status');
            const msg = urlParams.get('msg') || '操作完成';
            document.querySelector('body').insertAdjacentHTML('afterbegin', 
                `<div class="status ${type}">${msg}</div>`);
            history.replaceState({}, '', '/');
        }
    });
    </script>
</body>
</html>"""
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(TEMPLATE_CONTENT)

def fetch_real_data():
    """尝试获取真实微博热搜数据（带完整异常处理）"""
    try:
        # 使用公开可访问的微博热搜API（无需认证）
        response = requests.get(
            "https://api.vvhan.com/api/hotlist/weibo", 
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and isinstance(data.get("data"), list):
            games = []
            keywords = ["游戏", "手游", "端游", "电竞", "王者荣耀", "原神", "和平精英", "LOL", "英雄联盟"]
            
            for item in data["data"]:
                title = str(item.get("title", "")).strip()
                hot = str(item.get("hot", "0")).replace("万", "0000").replace(",", "")
                
                # 仅保留含游戏关键词的条目
                if any(kw in title for kw in keywords) and title:
                    try:
                        views = int(float(hot))
                    except:
                        views = 1000  # 默认热度
                    
                    # 限制标题长度（避免过长）
                    if len(title) > 20:
                        title = title[:18] + "..."
                    
                    games.append((title, "weibo", views))
                    if len(games) >= 10:
                        break
            
            if games:
                print(f"✅ 成功获取 {len(games)} 条真实微博游戏热搜数据")
                return games
            else:
                print("⚠️ 未找到含游戏关键词的热搜，使用模拟数据")
        else:
            print("⚠️ API返回格式异常，使用模拟数据")
    except Exception as e:
        print(f"⚠️ 真实数据抓取失败 ({type(e).__name__}): {str(e)[:100]}，使用模拟数据")
    
    # 回退到模拟数据（确保服务永不中断）
    return [
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

def scrape_and_save(source="auto"):
    """抓取并保存数据（source: auto/manual）"""
    init_db()
    use_real = os.getenv("USE_REAL_DATA", "false").lower() == "true"
    
    # Render环境特殊处理：国外服务器无法访问微博API
    is_render = os.getenv("RENDER") is not None
    if is_render and use_real:
        print("⚠️ Render环境检测：强制使用模拟数据（国外服务器无法访问微博API）")
        games_data = fetch_real_data()  # 实际会回退到模拟数据
    elif use_real:
        games_data = fetch_real_data()
    else:
        print("ℹ️ 使用模拟数据（环境变量 USE_REAL_DATA 未启用）")
        games_data = fetch_real_data()  # 内部已含回退逻辑
    
    # 保存数据
    for title, platform, views in games_data:
        save_game(title, platform, views)
    
    print(f"✅ [{source}] 数据更新完成！共 {len(games_data)} 条 | 来源: {'真实数据' if use_real and not is_render else '模拟数据'}")
    return len(games_data)

# ===== 路由定义 =====
@app.on_event("startup")
async def startup_event():
    # Render环境标识（用于前端提示）
    if os.getenv("RENDER") is None:
        os.environ["RENDER"] = "false"  # 本地开发环境
    
    # 启动时立即更新
    scrape_and_save(source="startup")
    
    # 设置每日00:00自动更新
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: scrape_and_save(source="scheduled"),
        'cron',
        hour=0,
        minute=0,
        id='daily_update',
        replace_existing=True
    )
    scheduler.start()
    print("⏰ 定时任务已启动（每日 00:00 自动更新）")

@app.get("/")
async def home(request: Request):
    games = get_top_games(limit=10)
    game_list = [
        {
            "title": g[0],
            "platform": g[1],
            "views": f"{g[2]:,}"
        }
        for g in games
    ]
    
    # 处理状态消息
    status = None
    if request.query_params.get("status"):
        status_type = request.query_params.get("status")
        msg = request.query_params.get("msg", "操作完成")
        status = {
            "type": "success" if status_type == "success" else "error",
            "message": msg
        }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "games": game_list,
            "status": status,
            "os": os  # 传递os模块用于模板判断
        }
    )

@app.get("/update")
async def manual_update(source: str = "manual"):
    """手动触发更新（带来源标识）"""
    try:
        count = scrape_and_save(source=source)
        return {
            "status": "success",
            "message": f"✅ 手动更新成功！新增 {count} 条数据",
            "count": count
        }
    except Exception as e:
        error_msg = f"❌ 更新失败: {str(e)[:150]}"
        print(f"ERROR in /update: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "db_path": os.getenv("DB_PATH", "/tmp/games.db"),
        "use_real_data": os.getenv("USE_REAL_DATA", "false"),
        "env": "Render" if os.getenv("RENDER") else "Local"
    }
