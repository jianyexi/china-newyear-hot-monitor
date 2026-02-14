import httpx
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class ZhihuScraper(BaseScraper):
    """知乎热榜爬虫"""

    platform = "zhihu"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        resp = await client.get(url, params={"limit": 50})
        resp.raise_for_status()
        data = resp.json()

        topics: list[HotTopicCreate] = []
        for i, item in enumerate(data.get("data", []), start=1):
            target = item.get("target", {})
            title = target.get("title", "")
            if not title:
                continue
            topics.append(
                HotTopicCreate(
                    platform=self.platform,
                    title=title,
                    url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                    rank=i,
                    hot_value=int(item.get("detail_text", "0").replace("万热度", "0000").replace(" 热度", "")),
                    category=None,
                    is_cny_related=self._is_cny_related(title),
                )
            )
        return topics
