import httpx
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class DouyinScraper(BaseScraper):
    """抖音热搜爬虫"""

    platform = "douyin"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        topics: list[HotTopicCreate] = []
        word_list = data.get("data", {}).get("word_list", [])
        for i, item in enumerate(word_list[:50], start=1):
            title = item.get("word", "")
            if not title:
                continue
            topics.append(
                HotTopicCreate(
                    platform=self.platform,
                    title=title,
                    url=f"https://www.douyin.com/search/{title}",
                    rank=i,
                    hot_value=item.get("hot_value"),
                    category=item.get("word_type_str"),
                    is_cny_related=self._is_cny_related(title),
                )
            )
        return topics
