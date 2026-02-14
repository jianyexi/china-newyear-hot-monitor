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
    # 分类分析
    categories: list[CategoryBreakdown]
    # 跨平台热点（出现在多个平台）
    cross_platform_hot: list[dict]
    # 各平台独家洞察
    platform_insights: list[PlatformInsight]
    # 春节专题
    cny_summary: dict
    # AI 深度分析（如果配置了 LLM）
    ai_analysis: str | None = None
