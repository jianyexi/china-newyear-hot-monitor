import abc
import logging
import httpx
from app.config import get_effective_keywords
from app.schemas import HotTopicCreate

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """爬虫基类"""

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
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
                return await self._parse(client)
        except Exception as e:
            logger.warning("[%s] scrape error: %s", self.platform, e)
            return []

    @abc.abstractmethod
    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        ...
