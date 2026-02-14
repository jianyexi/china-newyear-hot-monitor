import os
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/hot_monitor",
    )
    # 抓取配置
    SCRAPE_INTERVAL_MINUTES: int = 30
    SCRAPE_TOP_N: int = 50
    ENABLED_PLATFORMS: list[str] = ["weibo", "zhihu", "baidu", "douyin", "xiaohongshu"]
    # API 安全
    API_KEY: str | None = os.getenv("API_KEY", None)  # 设置后需携带 X-API-Key 头
    RATE_LIMIT_PER_MINUTE: int = 60
    # OpenAI API（可选）
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY", None)
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # 春节相关关键词
    CNY_KEYWORDS: list[str] = [
        "春节", "过年", "除夕", "春晚", "年夜饭", "拜年", "红包", "压岁钱",
        "烟花", "爆竹", "庙会", "灯笼", "对联", "福字", "团圆", "年货",
        "春运", "回家", "龙年", "蛇年", "虎年", "兔年", "马年", "羊年",
        "猴年", "鸡年", "狗年", "猪年", "鼠年", "牛年",
    ]
    CUSTOM_KEYWORDS: list[str] = []
    ANALYSIS_ENABLED: bool = True

    class Config:
        env_file = ".env"


# 配置更新的校验 Schema
class ConfigUpdate(BaseModel):
    scrape_interval_minutes: int | None = Field(None, ge=5, le=1440)
    scrape_top_n: int | None = Field(None, ge=10, le=100)
    enabled_platforms: list[str] | None = None
    cny_keywords: list[str] | None = None
    custom_keywords: list[str] | None = None
    analysis_enabled: bool | None = None
    openai_model: str | None = None


VALID_PLATFORMS = {"weibo", "zhihu", "baidu", "douyin", "xiaohongshu"}


settings = Settings()


# ---- 运行时可变配置（不重启生效） ----
_runtime_overrides: dict = {}


def get_runtime_config() -> dict:
    """获取当前完整运行时配置"""
    return {
        "scrape_interval_minutes": _runtime_overrides.get("scrape_interval_minutes", settings.SCRAPE_INTERVAL_MINUTES),
        "scrape_top_n": _runtime_overrides.get("scrape_top_n", settings.SCRAPE_TOP_N),
        "enabled_platforms": _runtime_overrides.get("enabled_platforms", settings.ENABLED_PLATFORMS),
        "cny_keywords": _runtime_overrides.get("cny_keywords", settings.CNY_KEYWORDS),
        "custom_keywords": _runtime_overrides.get("custom_keywords", settings.CUSTOM_KEYWORDS),
        "analysis_enabled": _runtime_overrides.get("analysis_enabled", settings.ANALYSIS_ENABLED),
        "openai_model": _runtime_overrides.get("openai_model", settings.OPENAI_MODEL),
        "openai_configured": bool(settings.OPENAI_API_KEY),
    }


def update_runtime_config(updates: dict) -> dict:
    """更新运行时配置，带校验"""
    validated = ConfigUpdate(**updates)
    update_dict = validated.model_dump(exclude_none=True)

    # 校验平台名
    if "enabled_platforms" in update_dict:
        invalid = set(update_dict["enabled_platforms"]) - VALID_PLATFORMS
        if invalid:
            raise ValueError(f"无效平台: {invalid}. 可选: {VALID_PLATFORMS}")
        if not update_dict["enabled_platforms"]:
            raise ValueError("至少启用一个平台")

    for key, value in update_dict.items():
        _runtime_overrides[key] = value
    return get_runtime_config()


def get_effective_keywords() -> list[str]:
    """获取生效的所有监控关键词（春节 + 自定义）"""
    cfg = get_runtime_config()
    return list(set(cfg["cny_keywords"] + cfg["custom_keywords"]))


def get_enabled_platforms() -> list[str]:
    """获取启用的平台列表"""
    return get_runtime_config()["enabled_platforms"]


def get_scrape_top_n() -> int:
    return get_runtime_config()["scrape_top_n"]
