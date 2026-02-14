import httpx
from app.schemas import HotTopicCreate
from app.scrapers.base import BaseScraper


class ZhihuScraper(BaseScraper):
    """知乎热榜爬虫"""

    platform = "zhihu"

    async def _parse(self, client: httpx.AsyncClient) -> list[HotTopicCreate]:
        topics: list[HotTopicCreate] = []

        # 方式1: 知乎热榜 API
        try:
            headers = {
                **self._get_headers(),
                "Referer": "https://www.zhihu.com/hot",
                "Cookie": "_zap=placeholder",
            }
            resp = await client.get(
                "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
                params={"limit": 50},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            for i, item in enumerate(data.get("data", []), start=1):
                target = item.get("target", {})
                title = target.get("title", "")
                if not title:
                    continue
                try:
                    text = item.get("detail_text", "0").replace(" 热度", "").strip()
                    if "万" in text:
                        hot_val = int(float(text.replace("万", "")) * 10000)
                    else:
                        hot_val = int(text)
                except (ValueError, AttributeError):
                    hot_val = None
                topics.append(
                    HotTopicCreate(
                        platform=self.platform,
                        title=title,
                        url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                        rank=i,
                        hot_value=hot_val,
                        category=None,
                        is_cny_related=self._is_cny_related(title),
                    )
                )
            if topics:
                return topics
        except Exception:
            pass

        # 方式2: 通过 Tophub 聚合
        try:
            from bs4 import BeautifulSoup

            resp = await client.get("https://tophub.today/n/mproPpoq6O")
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("table tr td a")
            for i, item in enumerate(items[:50], start=1):
                title = item.get_text(strip=True)
                if not title:
                    continue
                href = item.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://tophub.today{href}"
                topics.append(
                    HotTopicCreate(
                        platform=self.platform,
                        title=title,
                        url=href,
                        rank=i,
                        hot_value=None,
                        category=None,
                        is_cny_related=self._is_cny_related(title),
                    )
                )
        except Exception:
            pass

        return topics
