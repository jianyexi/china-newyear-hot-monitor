import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, Index, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HotTopic(Base):
    __tablename__ = "hot_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, comment="平台: weibo/zhihu/baidu/douyin/xiaohongshu")
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="热搜标题")
    url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原始链接")
    rank: Mapped[int] = mapped_column(Integer, nullable=False, comment="排名")
    hot_value: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="热度值")
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="分类标签")
    is_cny_related: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否春节相关")
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="情感: positive/neutral/negative")
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="情感分数 -1~1")
    dedup_key: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="去重 hash key")
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False, comment="抓取时间"
    )

    __table_args__ = (
        Index("ix_platform_fetched", "platform", "fetched_at"),
        Index("ix_cny_related", "is_cny_related", "fetched_at"),
        Index("ix_dedup_key", "dedup_key"),
        Index("ix_title_search", "title"),
    )

    def __repr__(self) -> str:
        return f"<HotTopic {self.platform}#{self.rank}: {self.title}>"


class TopicLifecycle(Base):
    """话题生命周期追踪"""
    __tablename__ = "topic_lifecycle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    peak_time: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    peak_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peak_hot_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    appearances: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="rising", comment="rising/peak/falling/off")

    __table_args__ = (
        Index("ix_lifecycle_status", "status"),
        Index("ix_lifecycle_last_seen", "last_seen"),
    )


class DailyReport(Base):
    """每日/每周分析报告"""
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    report_type: Mapped[str] = mapped_column(String(10), default="daily", comment="daily/weekly")
    total_topics: Mapped[int] = mapped_column(Integer, default=0)
    platforms_covered: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON list")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Markdown report content")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("report_date", "report_type", name="uq_report_date_type"),
    )


class AlertRule(Base):
    """告警规则"""
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="spike/keyword/failure")
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON rule config")
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
