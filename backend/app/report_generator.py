"""
每日/每周自动报告生成器
"""

import datetime
import json
import logging

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HotTopic, DailyReport
from app.analyzer import generate_analysis
from app.schemas import HotTopicOut

logger = logging.getLogger(__name__)


async def generate_daily_report(db: AsyncSession, report_date: str | None = None) -> DailyReport | None:
    """生成每日报告"""
    if not report_date:
        report_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # 检查是否已存在
    existing = (await db.execute(
        select(DailyReport).where(DailyReport.report_date == report_date, DailyReport.report_type == "daily")
    )).scalar()
    if existing:
        return existing

    # 获取当天数据
    day_start = datetime.datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    day_end = day_start + datetime.timedelta(days=1)

    query = select(HotTopic).where(
        HotTopic.fetched_at >= day_start,
        HotTopic.fetched_at < day_end,
    ).order_by(HotTopic.fetched_at.desc(), HotTopic.rank)

    result = await db.execute(query)
    all_topics = result.scalars().all()

    if not all_topics:
        return None

    # 取最近一批做分析
    latest_time = max(t.fetched_at for t in all_topics)
    latest_topics = [HotTopicOut.model_validate(t) for t in all_topics if t.fetched_at == latest_time]

    analysis = await generate_analysis(latest_topics)

    platforms = list({t.platform for t in all_topics})
    total_unique = len({t.title for t in all_topics})

    # 生成 Markdown 报告
    lines = [
        f"# 📊 热搜日报 — {report_date}",
        "",
        f"## 概览",
        f"- 监控平台：{', '.join(platforms)}",
        f"- 总抓取话题数：{len(all_topics)}",
        f"- 去重话题数：{total_unique}",
        f"- 春节相关占比：{analysis.cny_summary.get('ratio', 0) * 100:.1f}%",
        "",
        f"## 分类分布",
    ]

    for cat in analysis.categories[:8]:
        lines.append(f"- {cat.category}: {cat.count} 条 ({cat.percentage}%)")

    lines.append("")
    lines.append("## 跨平台热点")
    if analysis.cross_platform_hot:
        for hot in analysis.cross_platform_hot[:5]:
            titles = list(hot.get("titles", {}).values())
            lines.append(f"- 🔥 {titles[0] if titles else hot.get('keyword', '')}")
            lines.append(f"  出现在：{', '.join(hot.get('platforms', []))}")
    else:
        lines.append("- 当日无跨平台共同热点")

    if analysis.sentiment_summary:
        lines.append("")
        lines.append("## 舆论情绪")
        ss = analysis.sentiment_summary
        lines.append(f"- 正面: {ss.get('positive', 0)} 条 | 中性: {ss.get('neutral', 0)} 条 | 负面: {ss.get('negative', 0)} 条")

    if analysis.ai_analysis:
        lines.append("")
        lines.append("## AI 深度分析")
        lines.append(analysis.ai_analysis)

    summary = "\n".join(lines)

    report = DailyReport(
        report_date=report_date,
        report_type="daily",
        total_topics=total_unique,
        platforms_covered=json.dumps(platforms),
        summary=summary,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    logger.info("Generated daily report for %s", report_date)
    return report
