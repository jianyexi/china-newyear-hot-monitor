import httpx
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class DouyinScraper(BaseScraper):
    """抖音热搜爬虫 - 使用第三方聚合 API 作为备选"""

    platform = "douyin"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        topics: list[HotTopicCreate] = []

        # 方式1: 尝试抖音官方接口
        try:
            url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
            headers = {**self.headers, "Referer": "https://www.douyin.com/"}
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
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
            if topics:
                return topics
        except Exception:
            pass

        # 方式2: 使用 Tophub 聚合热搜
        try:
            from bs4 import BeautifulSoup

            resp = await client.get("https://tophub.today/n/DpQvNABoNE")
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("table tr td a")
            for i, item in enumerate(items[:50], start=1):
                title = item.get_text(strip=True)
                if not title:
                    continue
                topics.append(
                    HotTopicCreate(
                        platform=self.platform,
                        title=title,
                        url=f"https://www.douyin.com/search/{title}",
                        rank=i,
                        hot_value=None,
                        category=None,
                        is_cny_related=self._is_cny_related(title),
                    )
                )
        except Exception:
            pass

        return topics
