import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HotTopic(Base):
    __tablename__ = "hot_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, comment="平台: weibo/zhihu/baidu/douyin")
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="热搜标题")
    url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原始链接")
    rank: Mapped[int] = mapped_column(Integer, nullable=False, comment="排名")
    hot_value: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="热度值")
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="分类标签")
    is_cny_related: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否春节相关")
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False, comment="抓取时间"
    )

    __table_args__ = (
        Index("ix_platform_fetched", "platform", "fetched_at"),
        Index("ix_cny_related", "is_cny_related", "fetched_at"),
    )

    def __repr__(self) -> str:
        return f"<HotTopic {self.platform}#{self.rank}: {self.title}>"
