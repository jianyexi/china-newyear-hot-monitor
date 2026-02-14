import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import HotTopic
from app.schemas import HotTopicOut, PlatformStats, TrendItem, AnalysisReport

router = APIRouter(prefix="/api", tags=["hot-topics"])


@router.get("/topics", response_model=list[HotTopicOut])
async def get_topics(
    platform: str | None = Query(None, description="平台过滤"),
    cny_only: bool = Query(False, description="仅春节相关"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取最新热搜列表"""
    # 取最近一次抓取时间
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
    return result.scalars().all()


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
