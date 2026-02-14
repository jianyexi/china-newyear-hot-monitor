import httpx
from bs4 import BeautifulSoup
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class XiaohongshuScraper(BaseScraper):
    """小红书热搜爬虫"""

    platform = "xiaohongshu"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        topics: list[HotTopicCreate] = []

        # 方式1: 小红书热搜页面
        try:
            resp = await client.get(
                "https://www.xiaohongshu.com/explore",
                headers={
                    **self._get_headers(),
                    "Referer": "https://www.xiaohongshu.com/",
                },
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(".hot-item, .trending-item, [class*='hot'] a")
            for i, item in enumerate(items[:50], start=1):
                title = item.get_text(strip=True)
                if not title:
                    continue
                topics.append(
                    HotTopicCreate(
                        platform=self.platform,
                        title=title,
                        url=f"https://www.xiaohongshu.com/search_result?keyword={title}",
                        rank=i,
                        hot_value=None,
                        category=None,
                        is_cny_related=self._is_cny_related(title),
                    )
                )
            if topics:
                return topics
        except Exception:
            pass

        # 方式2: Tophub 聚合
        try:
            resp = await client.get("https://tophub.today/n/L4MdA5ldxD")
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("table tr td a")
            rank = 0
            for item in items:
                title = item.get_text(strip=True)
                if not title or len(title) < 2:
                    continue
                rank += 1
                href = item.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://tophub.today{href}"
                topics.append(
                    HotTopicCreate(
                        platform=self.platform,
                        title=title,
                        url=href,
                        rank=rank,
                        hot_value=None,
                        category=None,
                        is_cny_related=self._is_cny_related(title),
                    )
                )
                if rank >= 50:
                    break
        except Exception:
            pass

        return topics
