import abc
import asyncio
import logging
import httpx
from app.config import get_effective_keywords
from app.schemas import HotTopicCreate

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]  # 秒


class BaseScraper(abc.ABC):
    """爬虫基类，含指数退避重试"""

    platform: str = ""
    headers: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    def _is_cny_related(self, title: str) -> bool:
        return any(kw in title for kw in get_effective_keywords())

    async def fetch(self) -> list[HotTopicCreate]:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    headers=self.headers, timeout=20, follow_redirects=True
                ) as client:
                    result = await self._parse(client)
                    if result:
                        if attempt > 0:
                            logger.info("[%s] succeeded on retry #%d", self.platform, attempt)
                        return result
                    # 空结果也算成功，不重试
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
