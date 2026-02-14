import datetime
from pydantic import BaseModel


class HotTopicBase(BaseModel):
    platform: str
    title: str
    url: str | None = None
    rank: int
    hot_value: int | None = None
    category: str | None = None
    is_cny_related: bool = False


class HotTopicCreate(HotTopicBase):
    pass


class HotTopicOut(HotTopicBase):
    id: int
    fetched_at: datetime.datetime

    class Config:
        from_attributes = True


class TrendItem(BaseModel):
    title: str
    platform: str
    hot_values: list[int]
    timestamps: list[datetime.datetime]


class PlatformStats(BaseModel):
    platform: str
    total_topics: int
    cny_related: int
    latest_fetch: datetime.datetime | None
