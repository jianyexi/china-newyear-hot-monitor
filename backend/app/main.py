import asyncio
import datetime
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings, get_enabled_platforms
from app.cache import cache_delete
from app.database import init_db, async_session
from app.models import HotTopic
from app.api.routes import router
from app.scrapers.weibo import WeiboScraper
from app.scrapers.zhihu import ZhihuScraper
from app.scrapers.baidu import BaiduScraper
from app.scrapers.douyin import DouyinScraper
from app.scrapers.xiaohongshu import XiaohongshuScraper

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ALL_SCRAPERS = {
    "weibo": WeiboScraper(),
    "zhihu": ZhihuScraper(),
    "baidu": BaiduScraper(),
    "douyin": DouyinScraper(),
    "xiaohongshu": XiaohongshuScraper(),
}
scheduler = AsyncIOScheduler()
_app_start_time = time.time()
_scrape_count = 0
_last_scrape_status: dict = {}


# ---- 限流中间件 ----
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_per_minute: int = 60):
        super().__init__(app)
        self.max_per_minute = max_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # 清除超过 60 秒的记录
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
        if len(self.requests[client_ip]) >= self.max_per_minute:
            return Response(
                content='{"detail":"请求过于频繁，请稍后再试"}',
                status_code=429,
                media_type="application/json",
            )
        self.requests[client_ip].append(now)
        return await call_next(request)


# ---- API Key 认证中间件 ----
class ApiKeyMiddleware(BaseHTTPMiddleware):
    OPEN_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health"}

    async def dispatch(self, request: Request, call_next):
        if not settings.API_KEY:
            return await call_next(request)
        if request.url.path in self.OPEN_PATHS:
            return await call_next(request)
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.API_KEY:
            return Response(
                content='{"detail":"无效的 API Key，请在请求头添加 X-API-Key"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


async def run_scrapers():
    """执行启用的爬虫并保存数据"""
    global _scrape_count, _last_scrape_status
    now = datetime.datetime.now(datetime.timezone.utc)
    enabled = get_enabled_platforms()
    active_scrapers = [s for name, s in ALL_SCRAPERS.items() if name in enabled]
    logger.info("Starting scrape cycle... (platforms: %s)", ", ".join(enabled))

    results = await asyncio.gather(*(s.fetch() for s in active_scrapers), return_exceptions=True)

    platform_status = {}
    async with async_session() as session:
        try:
            count = 0
            for scraper, items in zip(active_scrapers, results):
                if isinstance(items, Exception):
                    logger.warning("Scraper error: %s", items)
                    platform_status[scraper.platform] = {"status": "error", "count": 0, "error": str(items)}
                    continue
                platform_status[scraper.platform] = {"status": "ok", "count": len(items)}
                for item in items:
                    topic = HotTopic(**item.model_dump(), fetched_at=now)
                    session.add(topic)
                    count += 1
            await session.commit()
            logger.info("Saved %d topics.", count)
        except Exception as e:
            await session.rollback()
            logger.error("Failed to save topics: %s", e)

    _scrape_count += 1
    _last_scrape_status = {
        "time": now.isoformat(),
        "total_saved": sum(p.get("count", 0) for p in platform_status.values()),
        "platforms": platform_status,
    }
    # 清除缓存
    cache_delete()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await run_scrapers()
    scheduler.add_job(run_scrapers, "interval", minutes=settings.SCRAPE_INTERVAL_MINUTES)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="中国过年热点舆论监控平台",
    description="自动抓取微博/知乎/百度/抖音/小红书热搜，聚焦春节相关话题",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, max_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(ApiKeyMiddleware)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "中国过年热点舆论监控平台 API", "docs": "/docs"}


@app.get("/health")
async def health():
    """健康检查 + 系统状态"""
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - _app_start_time),
        "scrape_count": _scrape_count,
        "last_scrape": _last_scrape_status or None,
        "enabled_platforms": get_enabled_platforms(),
    }
