import asyncio
import datetime
import json
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings, get_enabled_platforms
from app.cache import cache_delete
from app.database import init_db, async_session
from app.dedup import make_dedup_key
from app.sentiment import analyze_sentiment
from app.models import HotTopic, TopicLifecycle, AlertRule
from app.schemas import HotTopicOut
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

# ---- WebSocket 连接管理 ----
_ws_clients: set[WebSocket] = set()


async def ws_broadcast(data: dict):
    """广播消息给所有 WebSocket 客户端"""
    dead = set()
    msg = json.dumps(data, ensure_ascii=False, default=str)
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _ws_clients -= dead


# ---- 限流中间件 ----
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_per_minute: int = 60):
        super().__init__(app)
        self.max_per_minute = max_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
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
    OPEN_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health", "/ws"}

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


# ---- 获取上一轮抓取数据（用于告警对比）----
_previous_topics: list[HotTopicOut] = []


async def run_scrapers():
    """执行启用的爬虫并保存数据，含去重、情感分析、生命周期、告警"""
    global _scrape_count, _last_scrape_status, _previous_topics
    now = datetime.datetime.now(datetime.timezone.utc)
    enabled = get_enabled_platforms()
    active_scrapers = [s for name, s in ALL_SCRAPERS.items() if name in enabled]
    logger.info("Starting scrape cycle... (platforms: %s)", ", ".join(enabled))

    results = await asyncio.gather(*(s.fetch() for s in active_scrapers), return_exceptions=True)

    platform_status = {}
    scrape_errors = {}
    new_topics: list[HotTopicOut] = []

    async with async_session() as session:
        try:
            count = 0
            dedup_count = 0

            # 获取最近 6 小时的 dedup_key 集合用于去重
            from sqlalchemy import select
            six_hours_ago = now - datetime.timedelta(hours=6)
            existing_keys = set()
            result = await session.execute(
                select(HotTopic.dedup_key).where(
                    HotTopic.fetched_at >= six_hours_ago,
                    HotTopic.dedup_key.isnot(None),
                )
            )
            existing_keys = {r[0] for r in result}

            for scraper, items in zip(active_scrapers, results):
                if isinstance(items, Exception):
                    logger.warning("Scraper error: %s", items)
                    platform_status[scraper.platform] = {"status": "error", "count": 0, "error": str(items)}
                    scrape_errors[scraper.platform] = str(items)
                    continue

                saved = 0
                for item in items:
                    # 去重检查
                    dk = make_dedup_key(item.platform, item.title)
                    if dk in existing_keys:
                        dedup_count += 1
                        continue

                    # 情感分析
                    sentiment_label, sentiment_score = analyze_sentiment(item.title)

                    topic = HotTopic(
                        **item.model_dump(),
                        fetched_at=now,
                        dedup_key=dk,
                        sentiment=sentiment_label,
                        sentiment_score=sentiment_score,
                    )
                    session.add(topic)
                    existing_keys.add(dk)
                    count += 1
                    saved += 1

                platform_status[scraper.platform] = {"status": "ok", "count": saved}

            await session.commit()
            logger.info("Saved %d topics (%d deduped).", count, dedup_count)

            # 获取本轮所有新增话题用于告警
            result2 = await session.execute(
                select(HotTopic).where(HotTopic.fetched_at == now).order_by(HotTopic.rank)
            )
            new_topics = [HotTopicOut.model_validate(t) for t in result2.scalars().all()]

            # 更新生命周期
            await _update_lifecycles(session, new_topics, now)

            # 处理告警
            await _process_alert_rules(session, new_topics, _previous_topics, scrape_errors)

        except Exception as e:
            await session.rollback()
            logger.error("Failed to save topics: %s", e)

    _previous_topics = new_topics
    _scrape_count += 1
    _last_scrape_status = {
        "time": now.isoformat(),
        "total_saved": sum(p.get("count", 0) for p in platform_status.values()),
        "deduped": dedup_count if 'dedup_count' in dir() else 0,
        "platforms": platform_status,
    }
    cache_delete()

    # WebSocket 广播新数据通知
    await ws_broadcast({
        "type": "scrape_complete",
        "time": now.isoformat(),
        "total": len(new_topics),
        "platforms": list(platform_status.keys()),
    })


async def _update_lifecycles(session, topics: list[HotTopicOut], now: datetime.datetime):
    """更新话题生命周期"""
    from sqlalchemy import select
    for t in topics:
        dk = make_dedup_key(t.platform, t.title)
        result = await session.execute(
            select(TopicLifecycle).where(TopicLifecycle.dedup_key == dk)
        )
        lifecycle = result.scalar()

        if lifecycle:
            lifecycle.last_seen = now
            lifecycle.appearances += 1
            if t.rank and (lifecycle.peak_rank is None or t.rank < lifecycle.peak_rank):
                lifecycle.peak_rank = t.rank
                lifecycle.peak_time = now
            if t.hot_value and (lifecycle.peak_hot_value is None or t.hot_value > lifecycle.peak_hot_value):
                lifecycle.peak_hot_value = t.hot_value
            # 状态判断
            if lifecycle.appearances <= 2:
                lifecycle.status = "rising"
            elif t.rank and lifecycle.peak_rank and t.rank <= lifecycle.peak_rank:
                lifecycle.status = "peak"
            else:
                lifecycle.status = "falling"
        else:
            lifecycle = TopicLifecycle(
                platform=t.platform,
                title=t.title,
                dedup_key=dk,
                first_seen=now,
                last_seen=now,
                peak_rank=t.rank,
                peak_time=now,
                peak_hot_value=t.hot_value,
                appearances=1,
                status="rising",
            )
            session.add(lifecycle)

    # 标记超过 2 小时未出现的话题为 off
    two_hours_ago = now - datetime.timedelta(hours=2)
    from sqlalchemy import update
    await session.execute(
        update(TopicLifecycle)
        .where(TopicLifecycle.last_seen < two_hours_ago, TopicLifecycle.status != "off")
        .values(status="off")
    )
    await session.commit()


async def _process_alert_rules(session, current, previous, errors):
    """处理告警规则"""
    from sqlalchemy import select
    from app.alerts import process_alerts

    result = await session.execute(
        select(AlertRule).where(AlertRule.enabled == True)  # noqa: E712
    )
    rules = result.scalars().all()
    if not rules:
        return

    rule_dicts = [
        {"name": r.name, "rule_type": r.rule_type, "config_json": r.config_json,
         "webhook_url": r.webhook_url, "enabled": r.enabled}
        for r in rules
    ]
    triggered = await process_alerts(current, previous, errors, rule_dicts)
    if triggered:
        logger.info("Alerts triggered: %d rules", len(triggered))


async def _generate_daily_report_job():
    """定时生成每日报告"""
    from app.report_generator import generate_daily_report
    async with async_session() as session:
        try:
            await generate_daily_report(session)
        except Exception as e:
            logger.error("Daily report generation failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await run_scrapers()
    scheduler.add_job(run_scrapers, "interval", minutes=settings.SCRAPE_INTERVAL_MINUTES)
    # 每天 23:55 生成日报
    scheduler.add_job(_generate_daily_report_job, "cron", hour=23, minute=55)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="中国过年热点舆论监控平台",
    description="自动抓取微博/知乎/百度/抖音/小红书热搜，聚焦春节相关话题",
    version="2.0.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, max_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(ApiKeyMiddleware)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "中国过年热点舆论监控平台 API v2.0", "docs": "/docs"}


@app.get("/health")
async def health():
    """健康检查 + 系统状态"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": round(time.time() - _app_start_time),
        "scrape_count": _scrape_count,
        "last_scrape": _last_scrape_status or None,
        "enabled_platforms": get_enabled_platforms(),
        "ws_clients": len(_ws_clients),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket 实时推送端点"""
    await ws.accept()
    _ws_clients.add(ws)
    logger.info("WebSocket client connected (%d total)", len(_ws_clients))
    try:
        while True:
            await ws.receive_text()  # keep-alive
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)
        logger.info("WebSocket client disconnected (%d remaining)", len(_ws_clients))
