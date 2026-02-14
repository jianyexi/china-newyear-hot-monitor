import httpx
from bs4 import BeautifulSoup
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class BaiduScraper(BaseScraper):
    """百度热搜爬虫"""

    platform = "baidu"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        url = "https://top.baidu.com/board?tab=realtime"
        resp = await client.get(url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        topics: list[HotTopicCreate] = []

        items = soup.select(".c-single-text-ellipsis")
        for i, item in enumerate(items[:50], start=1):
            title = item.get_text(strip=True)
            if not title:
                continue
            topics.append(
                HotTopicCreate(
                    platform=self.platform,
                    title=title,
                    url=f"https://www.baidu.com/s?wd={title}",
                    rank=i,
                    hot_value=None,
                    category=None,
                    is_cny_related=self._is_cny_related(title),
                )
            )
        return topics
