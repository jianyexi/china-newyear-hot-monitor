# 🧧 中国过年热点舆论监控平台

自动抓取中国主流平台春节期间热点话题的实时监控系统。

## ✨ 功能特性

- 📱 **多平台热搜抓取** — 微博、知乎、百度、抖音热搜榜
- ⏰ **定时自动采集** — 每 30 分钟自动抓取一次
- 🧧 **春节话题高亮** — 自动识别和标记春节相关话题
- 📈 **趋势分析** — 关键词热度变化趋势图表
- 📊 **数据统计** — 各平台话题数量、春节相关占比
- 🐳 **一键部署** — Docker Compose 一键启动

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 爬虫 | Python httpx + BeautifulSoup |
| 后端 | FastAPI + SQLAlchemy (async) |
| 数据库 | PostgreSQL |
| 定时任务 | APScheduler |
| 前端 | React + TypeScript + Ant Design + ECharts |
| 部署 | Docker Compose |

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd china-newyear-hot-monitor

# 一键启动
docker compose up -d

# 访问
# 前端: http://localhost
# API 文档: http://localhost:8000/docs
```

### 本地开发

**后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 确保 PostgreSQL 已运行
cp ../.env.example .env
uvicorn app.main:app --reload
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/topics` | GET | 获取最新热搜列表 |
| `/api/topics/history` | GET | 获取历史热搜数据 |
| `/api/trends?title=春晚` | GET | 获取话题热度趋势 |
| `/api/stats` | GET | 获取各平台统计信息 |

查看完整 API 文档：启动后访问 `http://localhost:8000/docs`

## 📁 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口 + 定时任务
│   │   ├── config.py        # 配置（春节关键词等）
│   │   ├── database.py      # PostgreSQL 连接
│   │   ├── models.py        # 数据模型
│   │   ├── schemas.py       # API 数据格式
│   │   ├── api/routes.py    # API 路由
│   │   └── scrapers/        # 各平台爬虫
│   │       ├── base.py      # 爬虫基类
│   │       ├── weibo.py     # 微博热搜
│   │       ├── zhihu.py     # 知乎热榜
│   │       ├── baidu.py     # 百度热搜
│   │       └── douyin.py    # 抖音热搜
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── services/api.ts  # API 调用
│   │   └── types/index.ts   # 类型定义
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## ⚙️ 配置

通过环境变量或 `.env` 文件配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/hot_monitor` | 数据库连接 |
| `SCRAPE_INTERVAL_MINUTES` | `30` | 抓取间隔（分钟） |

## 📄 License

MIT
