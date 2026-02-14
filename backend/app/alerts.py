"""
告警通知系统
- 突发热点检测（热度突增）
- 关键词告警
- 爬虫故障告警
- Webhook 推送（企业微信/钉钉/自定义）
"""

import json
import logging
import datetime

import httpx

from app.schemas import HotTopicOut

logger = logging.getLogger(__name__)


async def send_webhook(url: str, title: str, content: str) -> bool:
    """发送 Webhook 通知，自动检测企业微信/钉钉/通用格式"""
    if not url:
        return False
    try:
        if "qyapi.weixin" in url:
            # 企业微信
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": f"## {title}\n{content}"},
            }
        elif "oapi.dingtalk" in url:
            # 钉钉
            payload = {
                "msgtype": "markdown",
                "markdown": {"title": title, "text": f"## {title}\n{content}"},
            }
        else:
            # 通用 webhook
            payload = {"title": title, "content": content, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Webhook sent: %s", title)
            return True
    except Exception as e:
        logger.warning("Webhook failed (%s): %s", url[:50], e)
        return False


def detect_spikes(
    current_topics: list[HotTopicOut],
    previous_topics: list[HotTopicOut],
    threshold: float = 2.0,
) -> list[dict]:
    """检测热度突增的话题 (当前热度 > 上轮热度 * threshold)"""
    prev_map: dict[str, int] = {}
    for t in previous_topics:
        key = f"{t.platform}:{t.title}"
        prev_map[key] = t.hot_value or 0

    spikes = []
    for t in current_topics:
        key = f"{t.platform}:{t.title}"
        current_val = t.hot_value or 0
        prev_val = prev_map.get(key, 0)

        if prev_val > 0 and current_val > prev_val * threshold:
            spikes.append({
                "platform": t.platform,
                "title": t.title,
                "previous_value": prev_val,
                "current_value": current_val,
                "increase_ratio": round(current_val / prev_val, 2),
            })
        elif prev_val == 0 and t.rank <= 3:
            # 新上榜 Top3
            spikes.append({
                "platform": t.platform,
                "title": t.title,
                "previous_value": 0,
                "current_value": current_val,
                "increase_ratio": 0,
                "note": "新上榜 Top3",
            })

    return sorted(spikes, key=lambda x: x.get("increase_ratio", 0), reverse=True)


def check_keyword_alerts(
    topics: list[HotTopicOut],
    alert_keywords: list[str],
) -> list[dict]:
    """检查是否有匹配告警关键词的话题"""
    matches = []
    for t in topics:
        for kw in alert_keywords:
            if kw in t.title:
                matches.append({
                    "keyword": kw,
                    "platform": t.platform,
                    "title": t.title,
                    "rank": t.rank,
                })
    return matches


async def process_alerts(
    current_topics: list[HotTopicOut],
    previous_topics: list[HotTopicOut],
    scrape_errors: dict[str, str],
    alert_rules: list[dict],
) -> list[dict]:
    """处理所有告警规则，发送通知"""
    triggered: list[dict] = []

    for rule in alert_rules:
        if not rule.get("enabled", True):
            continue

        rule_type = rule.get("rule_type", "")
        config = json.loads(rule.get("config_json", "{}") or "{}")
        webhook_url = rule.get("webhook_url", "")

        if rule_type == "spike":
            threshold = config.get("threshold", 2.0)
            spikes = detect_spikes(current_topics, previous_topics, threshold)
            if spikes:
                content_lines = [f"- **{s['platform']}** [{s['title']}] 热度 {s.get('previous_value',0)} → {s['current_value']}" for s in spikes[:5]]
                await send_webhook(webhook_url, "🔥 热度突增告警", "\n".join(content_lines))
                triggered.append({"rule": rule["name"], "type": "spike", "count": len(spikes), "items": spikes[:5]})

        elif rule_type == "keyword":
            keywords = config.get("keywords", [])
            matches = check_keyword_alerts(current_topics, keywords)
            if matches:
                content_lines = [f"- [{m['keyword']}] {m['platform']} #{m['rank']} {m['title']}" for m in matches[:5]]
                await send_webhook(webhook_url, "🔔 关键词告警", "\n".join(content_lines))
                triggered.append({"rule": rule["name"], "type": "keyword", "count": len(matches), "items": matches[:5]})

        elif rule_type == "failure":
            if scrape_errors:
                content_lines = [f"- **{p}**: {err}" for p, err in scrape_errors.items()]
                await send_webhook(webhook_url, "⚠️ 爬虫故障告警", "\n".join(content_lines))
                triggered.append({"rule": rule["name"], "type": "failure", "errors": scrape_errors})

    return triggered
