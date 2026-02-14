import csv
import datetime
import io
import logging

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache_get, cache_set, cache_delete
from app.database import get_db
from app.models import HotTopic
from app.schemas import HotTopicOut, PlatformStats, TrendItem, AnalysisReport
from app.config import get_runtime_config, update_runtime_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["hot-topics"])


@router.get("/topics", response_model=list[HotTopicOut])
async def get_topics(
    platform: str | None = Query(None, description="平台过滤"),
    cny_only: bool = Query(False, description="仅春节相关"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取最新热搜列表"""
    cache_key = f"topics:{platform}:{cny_only}:{limit}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sub = select(func.max(HotTopic.fetched_at))
    if platform:
        sub = sub.where(HotTopic.platform == platform)
    latest_time = (await db.execute(sub)).scalar()
    if not latest_time:
        return []

    query = (
        select(HotTopic)
        .where(HotTopic.fetched_at == latest_time)
        .order_by(HotTopic.rank)
        .limit(limit)
    )
    if platform:
        query = query.where(HotTopic.platform == platform)
    if cny_only:
        query = query.where(HotTopic.is_cny_related == True)  # noqa: E712

    result = await db.execute(query)
    topics = result.scalars().all()
    cache_set(cache_key, topics, ttl_seconds=300)
    return topics


@router.get("/topics/history", response_model=list[HotTopicOut])
async def get_history(
    platform: str | None = Query(None),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """获取历史热搜"""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    query = (
        select(HotTopic)
        .where(HotTopic.fetched_at >= since)
        .order_by(HotTopic.fetched_at.desc(), HotTopic.rank)
        .limit(limit)
    )
    if platform:
        query = query.where(HotTopic.platform == platform)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/trends", response_model=list[TrendItem])
async def get_trends(
    title: str = Query(..., description="话题标题关键词"),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """获取话题趋势"""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    query = (
        select(HotTopic)
        .where(HotTopic.title.contains(title), HotTopic.fetched_at >= since)
        .order_by(HotTopic.fetched_at)
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    # 按 platform+title 分组
    groups: dict[str, TrendItem] = {}
    for row in rows:
        key = f"{row.platform}:{row.title}"
        if key not in groups:
            groups[key] = TrendItem(
                title=row.title, platform=row.platform, hot_values=[], timestamps=[]
            )
        groups[key].hot_values.append(row.hot_value or 0)
        groups[key].timestamps.append(row.fetched_at)

    return list(groups.values())


@router.get("/stats", response_model=list[PlatformStats])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """获取各平台统计"""
    cached = cache_get("stats")
    if cached is not None:
        return cached

    platforms = (await db.execute(select(distinct(HotTopic.platform)))).scalars().all()
    stats = []
    for p in platforms:
        total = (
            await db.execute(
                select(func.count()).where(HotTopic.platform == p)
            )
        ).scalar()
        cny = (
            await db.execute(
                select(func.count()).where(
                    HotTopic.platform == p, HotTopic.is_cny_related == True  # noqa: E712
                )
            )
        ).scalar()
        latest = (
            await db.execute(
                select(func.max(HotTopic.fetched_at)).where(HotTopic.platform == p)
            )
        ).scalar()
        stats.append(PlatformStats(platform=p, total_topics=total, cny_related=cny, latest_fetch=latest))
    cache_set("stats", stats, ttl_seconds=300)
    return stats


@router.get("/analysis", response_model=AnalysisReport)
async def get_analysis(db: AsyncSession = Depends(get_db)):
    """获取自动分析报告：分类统计、跨平台热点、春节专题、AI深度分析"""
    from app.analyzer import generate_analysis

    # 取最新一批数据
    latest_time = (await db.execute(select(func.max(HotTopic.fetched_at)))).scalar()
    if not latest_time:
        from app.schemas import AnalysisReport as AR
        import datetime
        return AR(
            generated_at=datetime.datetime.now(datetime.timezone.utc),
            total_topics=0, platforms_covered=[], categories=[],
            cross_platform_hot=[], platform_insights=[], cny_summary={},
        )

    query = select(HotTopic).where(HotTopic.fetched_at == latest_time).order_by(HotTopic.rank)
    result = await db.execute(query)
    topics = [HotTopicOut.model_validate(t) for t in result.scalars().all()]

    return await generate_analysis(topics)


# ---- 配置管理 API ----

@router.get("/config")
async def get_config():
    """获取当前系统配置"""
    return get_runtime_config()


@router.put("/config")
async def set_config(updates: dict = Body(...)):
    """更新运行时配置（不重启生效）"""
    try:
        new_config = update_runtime_config(updates)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=422, detail=str(e))
    cache_delete()  # 配置变更后清除缓存

    # 如果更新了抓取间隔，重新调度定时任务
    if "scrape_interval_minutes" in updates:
        from app.main import scheduler, run_scrapers
        jobs = scheduler.get_jobs()
        for job in jobs:
            scheduler.remove_job(job.id)
        scheduler.add_job(
            run_scrapers, "interval",
            minutes=new_config["scrape_interval_minutes"],
        )

    return {"message": "配置已更新", "config": new_config}


@router.post("/scrape")
async def trigger_scrape():
    """手动触发一次抓取"""
    import asyncio
    from app.main import run_scrapers
    asyncio.create_task(run_scrapers())
    return {"message": "抓取任务已触发，请稍后刷新查看结果"}


@router.get("/config/platforms")
async def get_available_platforms():
    """获取所有可用平台列表"""
    return {
        "available": [
            {"id": "weibo", "name": "微博", "icon": "📱"},
            {"id": "zhihu", "name": "知乎", "icon": "💬"},
            {"id": "baidu", "name": "百度", "icon": "🔍"},
            {"id": "douyin", "name": "抖音", "icon": "🎵"},
            {"id": "xiaohongshu", "name": "小红书", "icon": "📕"},
        ],
        "enabled": get_runtime_config()["enabled_platforms"],
    }


@router.get("/export/csv")
async def export_csv(
    platform: str | None = Query(None, description="平台过滤"),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """导出热搜数据为 CSV"""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    query = (
        select(HotTopic)
        .where(HotTopic.fetched_at >= since)
        .order_by(HotTopic.fetched_at.desc(), HotTopic.rank)
    )
    if platform:
        query = query.where(HotTopic.platform == platform)

    result = await db.execute(query)
    rows = result.scalars().all()

    output = io.StringIO()
    # Add BOM for Excel UTF-8 compatibility
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(["排名", "平台", "标题", "热度", "URL", "春节相关", "抓取时间"])
    for r in rows:
        writer.writerow([
            r.rank, r.platform, r.title, r.hot_value or "",
            r.url or "", "是" if r.is_cny_related else "否",
            r.fetched_at.isoformat() if r.fetched_at else "",
        ])

    output.seek(0)
    filename = f"hot_topics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
