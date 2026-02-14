import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 默认使用 PostgreSQL；设置 DATABASE_URL=sqlite+aiosqlite:///./hot_monitor.db 可用 SQLite 本地开发
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/hot_monitor",
    )
    SCRAPE_INTERVAL_MINUTES: int = 30
    # 春节相关关键词
    CNY_KEYWORDS: list[str] = [
        "春节", "过年", "除夕", "春晚", "年夜饭", "拜年", "红包", "压岁钱",
        "烟花", "爆竹", "庙会", "灯笼", "对联", "福字", "团圆", "年货",
        "春运", "回家", "龙年", "蛇年", "虎年", "兔年", "马年", "羊年",
        "猴年", "鸡年", "狗年", "猪年", "鼠年", "牛年",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
