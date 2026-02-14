import datetime
from pydantic import BaseModel, Field


class HotTopicBase(BaseModel):
    platform: str
    title: str
    url: str | None = None
    rank: int
    hot_value: int | None = None
    category: str | None = None
    is_cny_related: bool = False
    sentiment: str | None = None
    sentiment_score: float | None = None


class HotTopicCreate(HotTopicBase):
    pass


class HotTopicOut(HotTopicBase):
    id: int
    fetched_at: datetime.datetime
    dedup_key: str | None = None

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


# ---- 分析相关 ----

class CategoryBreakdown(BaseModel):
    """分类统计"""
    category: str
    count: int
    percentage: float
    top_topics: list[str]


class PlatformInsight(BaseModel):
    """平台维度洞察"""
    platform: str
    top_topics: list[str]
    cny_ratio: float
    unique_topics: list[str]


class AnalysisReport(BaseModel):
    """自动分析报告"""
    generated_at: datetime.datetime
    total_topics: int
    platforms_covered: list[str]
    categories: list[CategoryBreakdown]
    cross_platform_hot: list[dict]
    platform_insights: list[PlatformInsight]
    cny_summary: dict
    sentiment_summary: dict | None = None
    ai_analysis: str | None = None


# ---- 搜索相关 ----

class SearchQuery(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    platform: str | None = None
    hours: int = Field(default=24, ge=1, le=720)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[HotTopicOut]


# ---- 话题生命周期 ----

class TopicLifecycleOut(BaseModel):
    id: int
    platform: str
    title: str
    first_seen: datetime.datetime
    last_seen: datetime.datetime
    peak_time: datetime.datetime | None
    peak_rank: int | None
    peak_hot_value: int | None
    appearances: int
    status: str

    class Config:
        from_attributes = True


# ---- 每日报告 ----

class DailyReportOut(BaseModel):
    id: int
    report_date: str
    report_type: str
    total_topics: int
    summary: str | None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- 告警 ----

class AlertRuleCreate(BaseModel):
    name: str
    rule_type: str = Field(..., pattern="^(spike|keyword|failure)$")
    config_json: str | None = None
    webhook_url: str | None = None
    enabled: bool = True


class AlertRuleOut(AlertRuleCreate):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- 时间对比 ----

class CompareResult(BaseModel):
    period1: str
    period2: str
    new_topics: list[str]
    dropped_topics: list[str]
    rising_topics: list[dict]
    falling_topics: list[dict]
    common_count: int
