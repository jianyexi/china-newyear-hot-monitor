import asyncio
import datetime
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, async_session
from app.models import HotTopic
from app.api.routes import router
from app.scrapers.weibo import WeiboScraper
from app.scrapers.zhihu import ZhihuScraper
from app.scrapers.baidu import BaiduScraper
from app.scrapers.douyin import DouyinScraper
from app.scrapers.xiaohongshu import XiaohongshuScraper

scrapers = [WeiboScraper(), ZhihuScraper(), BaiduScraper(), DouyinScraper(), XiaohongshuScraper()]
scheduler = AsyncIOScheduler()


async def run_scrapers():
    """执行所有爬虫并保存数据"""
    now = datetime.datetime.utcnow()
    print(f"[{now}] Starting scrape cycle...")

    results = await asyncio.gather(*(s.fetch() for s in scrapers), return_exceptions=True)

    async with async_session() as session:
        count = 0
        for items in results:
            if isinstance(items, Exception):
                print(f"  Scraper error: {items}")
                continue
            for item in items:
                topic = HotTopic(**item.model_dump(), fetched_at=now)
                session.add(topic)
                count += 1
        await session.commit()
    print(f"  Saved {count} topics.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 启动时立即抓一次
    await run_scrapers()
    # 定时抓取
    scheduler.add_job(run_scrapers, "interval", minutes=settings.SCRAPE_INTERVAL_MINUTES)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="中国过年热点舆论监控平台",
    description="自动抓取微博/知乎/百度/抖音热搜，聚焦春节相关话题",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "中国过年热点舆论监控平台 API", "docs": "/docs"}
