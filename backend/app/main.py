import asyncio
import datetime
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, get_enabled_platforms
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


async def run_scrapers():
    """执行启用的爬虫并保存数据"""
    now = datetime.datetime.now(datetime.timezone.utc)
    enabled = get_enabled_platforms()
    active_scrapers = [s for name, s in ALL_SCRAPERS.items() if name in enabled]
    logger.info("Starting scrape cycle... (platforms: %s)", ", ".join(enabled))

    results = await asyncio.gather(*(s.fetch() for s in active_scrapers), return_exceptions=True)

    async with async_session() as session:
        try:
            count = 0
            for items in results:
                if isinstance(items, Exception):
                    logger.warning("Scraper error: %s", items)
                    continue
                for item in items:
                    topic = HotTopic(**item.model_dump(), fetched_at=now)
                    session.add(topic)
                    count += 1
            await session.commit()
            logger.info("Saved %d topics.", count)
        except Exception as e:
            await session.rollback()
            logger.error("Failed to save topics: %s", e)


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

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "中国过年热点舆论监控平台 API", "docs": "/docs"}
