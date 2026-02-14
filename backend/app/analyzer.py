"""
热搜自动分析引擎
- 规则分类：基于关键词将热搜归类到不同主题
- 跨平台对比：识别多平台共同热点
- 春节专题：春节相关话题深度分析
- LLM 深度分析（可选）：接入 OpenAI 兼容 API 进行智能摘要
"""

import datetime
import re
from collections import Counter

from app.config import settings
from app.schemas import (
    AnalysisReport,
    CategoryBreakdown,
    PlatformInsight,
    HotTopicOut,
)

# 主题分类关键词规则
CATEGORY_RULES: dict[str, list[str]] = {
    "🎬 影视娱乐": ["电影", "电视剧", "综艺", "明星", "演员", "导演", "票房", "春晚", "晚会", "歌手", "演唱", "MV", "剧", "上映", "首播"],
    "🏀 体育赛事": ["比赛", "冠军", "球队", "运动员", "奥运", "世界杯", "联赛", "冰壶", "短道速滑", "滑雪", "体育", "赛事", "金牌"],
    "💰 财经商业": ["股票", "基金", "经济", "市场", "企业", "公司", "营收", "利润", "涨", "跌", "投资", "融资", "IPO", "消费", "购金", "车贷"],
    "🌍 国际时事": ["美国", "俄", "欧盟", "日本", "韩国", "外交", "贸易", "制裁", "峰会", "国际", "海外", "中美", "中日", "中欧", "马六甲"],
    "📱 科技数码": ["AI", "人工智能", "手机", "芯片", "机器人", "互联网", "数字", "算法", "大模型", "科技", "DeepSeek", "量产"],
    "🏛️ 时政民生": ["政府", "政策", "改革", "民生", "教育", "医疗", "就业", "住房", "通报", "调查", "投案", "省政府", "立场", "王毅"],
    "🧧 春节年俗": settings.CNY_KEYWORDS,
    "😊 社会热议": ["热搜", "网友", "吐槽", "争议", "热议", "回应", "走红", "翻唱", "流浪", "大鹅", "喊话"],
    "🚗 出行交通": ["春运", "高铁", "机票", "火车", "12306", "航班", "出行", "旅客", "回家"],
}


def _classify_topic(title: str) -> str:
    """根据关键词规则对话题分类"""
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in title for kw in keywords):
            return category
    return "📌 其他"


def _find_cross_platform(topics: list[HotTopicOut]) -> list[dict]:
    """找出跨平台共同热点（标题关键词相似）"""
    # 提取每个话题的核心词（去掉标点和短词）
    def extract_keywords(title: str) -> set[str]:
        # 提取2字以上的中文词组
        words = re.findall(r"[\u4e00-\u9fff]{2,4}", title)
        return set(words)

    platform_topics: dict[str, list[tuple[str, set[str]]]] = {}
    for t in topics:
        kws = extract_keywords(t.title)
        platform_topics.setdefault(t.platform, []).append((t.title, kws))

    cross_hot: list[dict] = []
    seen = set()
    platforms = list(platform_topics.keys())

    for i, p1 in enumerate(platforms):
        for t1_title, t1_kws in platform_topics[p1]:
            if t1_title in seen or len(t1_kws) < 2:
                continue
            matched_platforms = {p1: t1_title}
            for p2 in platforms[i + 1:]:
                for t2_title, t2_kws in platform_topics[p2]:
                    overlap = t1_kws & t2_kws
                    if len(overlap) >= 2:
                        matched_platforms[p2] = t2_title
                        break
            if len(matched_platforms) >= 2:
                seen.add(t1_title)
                cross_hot.append({
                    "keyword": "、".join(t1_kws),
                    "platforms": list(matched_platforms.keys()),
                    "titles": matched_platforms,
                    "platform_count": len(matched_platforms),
                })

    cross_hot.sort(key=lambda x: x["platform_count"], reverse=True)
    return cross_hot[:10]


def _build_platform_insights(topics: list[HotTopicOut]) -> list[PlatformInsight]:
    """各平台独特视角分析"""
    by_platform: dict[str, list[HotTopicOut]] = {}
    for t in topics:
        by_platform.setdefault(t.platform, []).append(t)

    insights = []
    for platform, ptopics in by_platform.items():
        titles = [t.title for t in ptopics]
        cny_count = sum(1 for t in ptopics if t.is_cny_related)
        # 找该平台独有的话题（其他平台没有相似标题）
        other_titles = {t.title for t in topics if t.platform != platform}
        unique = []
        for title in titles[:20]:
            kws = set(re.findall(r"[\u4e00-\u9fff]{2,4}", title))
            is_unique = True
            for ot in other_titles:
                other_kws = set(re.findall(r"[\u4e00-\u9fff]{2,4}", ot))
                if len(kws & other_kws) >= 2:
                    is_unique = False
                    break
            if is_unique:
                unique.append(title)

        insights.append(PlatformInsight(
            platform=platform,
            top_topics=titles[:5],
            cny_ratio=round(cny_count / max(len(ptopics), 1), 2),
            unique_topics=unique[:5],
        ))
    return insights


def _build_cny_summary(topics: list[HotTopicOut]) -> dict:
    """春节话题专题分析"""
    cny_topics = [t for t in topics if t.is_cny_related]
    if not cny_topics:
        return {"count": 0, "ratio": 0, "platforms": {}, "top_topics": [], "sub_themes": {}}

    by_platform = Counter(t.platform for t in cny_topics)

    # 春节子主题
    sub_themes: dict[str, list[str]] = {
        "🎭 春晚相关": [],
        "🏠 团圆回家": [],
        "🧨 年俗文化": [],
        "🎬 春节档电影": [],
        "🧧 红包压岁钱": [],
        "🔥 其他春节": [],
    }
    for t in cny_topics:
        title = t.title
        if any(kw in title for kw in ["春晚", "晚会", "节目单"]):
            sub_themes["🎭 春晚相关"].append(title)
        elif any(kw in title for kw in ["回家", "团圆", "春运", "过年"]):
            sub_themes["🏠 团圆回家"].append(title)
        elif any(kw in title for kw in ["年夜饭", "年货", "庙会", "灯笼", "对联", "除夕", "拜年"]):
            sub_themes["🧨 年俗文化"].append(title)
        elif any(kw in title for kw in ["电影", "票房", "春节档"]):
            sub_themes["🎬 春节档电影"].append(title)
        elif any(kw in title for kw in ["红包", "压岁钱"]):
            sub_themes["🧧 红包压岁钱"].append(title)
        else:
            sub_themes["🔥 其他春节"].append(title)

    # 过滤空子主题
    sub_themes = {k: v for k, v in sub_themes.items() if v}

    return {
        "count": len(cny_topics),
        "ratio": round(len(cny_topics) / max(len(topics), 1), 2),
        "platforms": dict(by_platform),
        "top_topics": [t.title for t in sorted(cny_topics, key=lambda x: x.rank)[:10]],
        "sub_themes": {k: v[:5] for k, v in sub_themes.items()},
    }


async def _llm_analysis(topics: list[HotTopicOut]) -> str | None:
    """调用 LLM 做深度分析（可选）"""
    if not settings.OPENAI_API_KEY:
        return None

    try:
        import httpx

        titles_by_platform: dict[str, list[str]] = {}
        for t in topics:
            titles_by_platform.setdefault(t.platform, []).append(f"{t.rank}. {t.title}")

        content_parts = []
        for platform, titles in titles_by_platform.items():
            content_parts.append(f"【{platform}热搜】\n" + "\n".join(titles[:20]))

        prompt = f"""以下是中国各大平台当前的热搜榜单（{datetime.datetime.now().strftime('%Y年%m月%d日')}），请从以下几个维度进行分析：

1. **舆论焦点概述**：当前最核心的社会关注点是什么？
2. **情绪倾向分析**：整体舆论情绪偏正面/中性/负面？哪些话题情绪最强烈？
3. **春节氛围洞察**：春节相关话题反映了哪些社会趋势和变化？
4. **跨平台差异**：不同平台的关注点有何不同？反映了什么用户画像差异？
5. **值得关注的信号**：有哪些潜在的舆情风险或值得持续关注的话题？

请用中文回答，简洁有力，每个维度2-3句话。

{chr(10).join(content_parts)}"""

        base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一位资深舆情分析师，擅长从热搜数据中提炼洞察。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[LLM Analysis Error] {e}")
        return f"⚠️ AI 分析暂不可用：{e}"


async def generate_analysis(topics: list[HotTopicOut]) -> AnalysisReport:
    """生成完整分析报告"""
    # 1. 分类统计
    category_counter: dict[str, list[str]] = {}
    for t in topics:
        cat = _classify_topic(t.title)
        category_counter.setdefault(cat, []).append(t.title)

    total = max(len(topics), 1)
    categories = [
        CategoryBreakdown(
            category=cat,
            count=len(titles),
            percentage=round(len(titles) / total * 100, 1),
            top_topics=titles[:5],
        )
        for cat, titles in sorted(category_counter.items(), key=lambda x: -len(x[1]))
    ]

    # 2. 跨平台热点
    cross_platform = _find_cross_platform(topics)

    # 3. 平台洞察
    platform_insights = _build_platform_insights(topics)

    # 4. 春节专题
    cny_summary = _build_cny_summary(topics)

    # 5. LLM 深度分析
    ai_analysis = await _llm_analysis(topics)

    return AnalysisReport(
        generated_at=datetime.datetime.utcnow(),
        total_topics=len(topics),
        platforms_covered=list({t.platform for t in topics}),
        categories=categories,
        cross_platform_hot=cross_platform,
        platform_insights=platform_insights,
        cny_summary=cny_summary,
        ai_analysis=ai_analysis,
    )
