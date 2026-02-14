import abc
import httpx
from app.config import settings
from app.schemas import HotTopicCreate


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
        return any(kw in title for kw in settings.CNY_KEYWORDS)

    async def fetch(self) -> list[HotTopicCreate]:
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
                return await self._parse(client)
        except Exception as e:
            print(f"[{self.platform}] scrape error: {e}")
            return []

    @abc.abstractmethod
    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        ...
