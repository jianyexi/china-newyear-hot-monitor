import httpx
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class WeiboScraper(BaseScraper):
    """微博热搜爬虫 - 使用官方 API"""

    platform = "weibo"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        topics: list[HotTopicCreate] = []
        realtime = data.get("data", {}).get("realtime", [])
        for i, item in enumerate(realtime[:50], start=1):
            title = item.get("word", "") or item.get("note", "")
            if not title:
                continue
            topics.append(
                HotTopicCreate(
                    platform=self.platform,
                    title=title,
                    url=f"https://s.weibo.com/weibo?q=%23{title}%23",
                    rank=i,
                    hot_value=item.get("raw_hot") or item.get("num"),
                    category=item.get("label_name"),
                    is_cny_related=self._is_cny_related(title),
                )
            )
        return topics
