import abc
import asyncio
import logging
import os
import random
import httpx
from app.config import get_effective_keywords
from app.schemas import HotTopicCreate

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

PROXY_URL = os.getenv("PROXY_URL", None)  # e.g. http://proxy:8080


class BaseScraper(abc.ABC):
    """爬虫基类，含 UA 轮换、代理支持、指数退避重试"""

    platform: str = ""

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _is_cny_related(self, title: str) -> bool:
        return any(kw in title for kw in get_effective_keywords())

    async def fetch(self) -> list[HotTopicCreate]:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                proxy = PROXY_URL if PROXY_URL else None
                async with httpx.AsyncClient(
                    headers=self._get_headers(),
                    timeout=20,
                    follow_redirects=True,
                    proxy=proxy,
                ) as client:
                    result = await self._parse(client)
                    if result:
                        if attempt > 0:
                            logger.info("[%s] succeeded on retry #%d", self.platform, attempt)
                        return result
                    return []
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF[attempt]
                    logger.warning(
                        "[%s] attempt %d/%d failed: %s, retrying in %ds...",
                        self.platform, attempt + 1, MAX_RETRIES, e, wait,
                    )
                    await asyncio.sleep(wait)
        logger.error("[%s] all %d attempts failed: %s", self.platform, MAX_RETRIES, last_error)
        return []

    @abc.abstractmethod
    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        ...
