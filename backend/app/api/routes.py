import csv
import datetime
import io
import json
import logging
import re
from collections import Counter

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, distinct, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache_get, cache_set, cache_delete
from app.database import get_db
from app.models import HotTopic, TopicLifecycle, DailyReport, AlertRule
from app.schemas import (
    HotTopicOut, PlatformStats, TrendItem, AnalysisReport,
    SearchResult, TopicLifecycleOut, DailyReportOut,
    AlertRuleCreate, AlertRuleOut, CompareResult,
)
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


# ---- 全文搜索 ----

@router.get("/search", response_model=SearchResult)
async def search_topics(
    keyword: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    platform: str | None = Query(None),
    hours: int = Query(24, ge=1, le=720),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """全文搜索热搜话题"""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    conditions = [HotTopic.fetched_at >= since, HotTopic.title.contains(keyword)]
    if platform:
        conditions.append(HotTopic.platform == platform)

    # 总数
    total = (await db.execute(select(func.count()).where(*conditions))).scalar() or 0

    # 分页查询
    query = (
        select(HotTopic)
        .where(*conditions)
        .order_by(HotTopic.fetched_at.desc(), HotTopic.rank)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = [HotTopicOut.model_validate(t) for t in result.scalars().all()]

    return SearchResult(total=total, page=page, page_size=page_size, items=items)


# ---- 话题生命周期 ----

@router.get("/lifecycle", response_model=list[TopicLifecycleOut])
async def get_lifecycle(
    status: str | None = Query(None, description="rising/peak/falling/off"),
    platform: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取话题生命周期数据"""
    query = select(TopicLifecycle).order_by(TopicLifecycle.last_seen.desc()).limit(limit)
    if status:
        query = query.where(TopicLifecycle.status == status)
    if platform:
        query = query.where(TopicLifecycle.platform == platform)
    result = await db.execute(query)
    return result.scalars().all()


# ---- 每日报告 ----

@router.get("/reports", response_model=list[DailyReportOut])
async def list_reports(
    report_type: str = Query("daily", description="daily/weekly"),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取报告列表"""
    query = (
        select(DailyReport)
        .where(DailyReport.report_type == report_type)
        .order_by(DailyReport.report_date.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/reports/{report_date}")
async def get_report(
    report_date: str,
    report_type: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定日期的报告"""
    result = await db.execute(
        select(DailyReport).where(
            DailyReport.report_date == report_date,
            DailyReport.report_type == report_type,
        )
    )
    report = result.scalar()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return DailyReportOut.model_validate(report)


@router.post("/reports/generate")
async def trigger_report(
    report_date: str = Query(None, description="YYYY-MM-DD，默认今天"),
    db: AsyncSession = Depends(get_db),
):
    """手动生成指定日期的报告"""
    from app.report_generator import generate_daily_report
    report = await generate_daily_report(db, report_date)
    if not report:
        raise HTTPException(status_code=404, detail="该日期无数据")
    return {"message": "报告已生成", "report_date": report.report_date}


# ---- 告警规则管理 ----

@router.get("/alerts", response_model=list[AlertRuleOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    """获取所有告警规则"""
    result = await db.execute(select(AlertRule).order_by(AlertRule.id))
    return result.scalars().all()


@router.post("/alerts", response_model=AlertRuleOut)
async def create_alert(rule: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    """创建告警规则"""
    alert = AlertRule(**rule.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """删除告警规则"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == alert_id))
    alert = result.scalar()
    if not alert:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    await db.delete(alert)
    await db.commit()
    return {"message": "已删除"}


# ---- 时间对比分析 ----

@router.get("/compare", response_model=CompareResult)
async def compare_periods(
    hours_ago_1: int = Query(0, ge=0, description="第一个时段：几小时前"),
    hours_ago_2: int = Query(24, ge=1, description="第二个时段：几小时前"),
    platform: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """对比两个时间段的热搜变化"""
    now = datetime.datetime.now(datetime.timezone.utc)

    async def get_period_topics(hours_ago: int) -> list[HotTopic]:
        target_time = now - datetime.timedelta(hours=hours_ago)
        sub = select(func.max(HotTopic.fetched_at)).where(HotTopic.fetched_at <= target_time)
        if platform:
            sub = sub.where(HotTopic.platform == platform)
        closest_time = (await db.execute(sub)).scalar()
        if not closest_time:
            return []
        query = select(HotTopic).where(HotTopic.fetched_at == closest_time)
        if platform:
            query = query.where(HotTopic.platform == platform)
        result = await db.execute(query)
        return list(result.scalars().all())

    topics1 = await get_period_topics(hours_ago_1)
    topics2 = await get_period_topics(hours_ago_2)

    titles1 = {t.title for t in topics1}
    titles2 = {t.title for t in topics2}
    rank_map1 = {t.title: t.rank for t in topics1}
    rank_map2 = {t.title: t.rank for t in topics2}

    new_topics = sorted(titles1 - titles2)[:20]
    dropped_topics = sorted(titles2 - titles1)[:20]

    common = titles1 & titles2
    rising = []
    falling = []
    for title in common:
        r1, r2 = rank_map1.get(title, 99), rank_map2.get(title, 99)
        if r1 < r2:
            rising.append({"title": title, "rank_before": r2, "rank_after": r1, "change": r2 - r1})
        elif r1 > r2:
            falling.append({"title": title, "rank_before": r2, "rank_after": r1, "change": r1 - r2})

    rising.sort(key=lambda x: x["change"], reverse=True)
    falling.sort(key=lambda x: x["change"], reverse=True)

    return CompareResult(
        period1=f"{hours_ago_1}h ago",
        period2=f"{hours_ago_2}h ago",
        new_topics=new_topics,
        dropped_topics=dropped_topics,
        rising_topics=rising[:10],
        falling_topics=falling[:10],
        common_count=len(common),
    )


# ---- 词云数据 ----

@router.get("/wordcloud")
async def get_wordcloud(
    hours: int = Query(24, ge=1, le=168),
    platform: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取词频数据（用于词云展示）"""
    cache_key = f"wordcloud:{platform}:{hours}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    query = select(HotTopic.title).where(HotTopic.fetched_at >= since)
    if platform:
        query = query.where(HotTopic.platform == platform)

    result = await db.execute(query)
    titles = [r[0] for r in result]

    # 提取词频
    word_counter: Counter = Counter()
    for title in titles:
        words = re.findall(r"[\u4e00-\u9fff]{2,4}", title)
        word_counter.update(words)

    # 过滤停用词
    stopwords = {"什么", "怎么", "为什么", "如何", "可以", "就是", "这个", "那个", "一个", "不是"}
    data = [
        {"name": word, "value": count}
        for word, count in word_counter.most_common(200)
        if word not in stopwords
    ]

    cache_set(cache_key, data, ttl_seconds=300)
    return data


# ---- 情感分析统计 ----

@router.get("/sentiment")
async def get_sentiment_stats(
    platform: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取情感分析统计"""
    latest_time = (await db.execute(select(func.max(HotTopic.fetched_at)))).scalar()
    if not latest_time:
        return {"positive": 0, "neutral": 0, "negative": 0, "details": []}

    query = select(HotTopic).where(HotTopic.fetched_at == latest_time)
    if platform:
        query = query.where(HotTopic.platform == platform)

    result = await db.execute(query)
    topics = result.scalars().all()

    sentiment_counts = Counter(t.sentiment or "neutral" for t in topics)
    details = [
        {
            "title": t.title,
            "platform": t.platform,
            "sentiment": t.sentiment or "neutral",
            "score": t.sentiment_score or 0,
            "rank": t.rank,
        }
        for t in sorted(topics, key=lambda x: abs(x.sentiment_score or 0), reverse=True)[:20]
    ]

    return {
        "positive": sentiment_counts.get("positive", 0),
        "neutral": sentiment_counts.get("neutral", 0),
        "negative": sentiment_counts.get("negative", 0),
        "total": len(topics),
        "details": details,
    }
