"""
情感分析模块 — 基于关键词规则的中文情感判断
"""

# 积极词汇
POSITIVE_WORDS = [
    "冠军", "成功", "突破", "创新", "暖心", "点赞", "夺冠", "感动", "团圆", "幸福",
    "好消息", "涨", "增长", "喜报", "恭喜", "祝福", "欢乐", "美好", "温暖", "惊喜",
    "丰收", "圆满", "胜利", "奇迹", "逆袭", "正能量", "治愈", "可爱", "浪漫", "甜蜜",
    "进步", "领先", "优秀", "精彩", "绝美", "太棒", "好评", "满意", "免费", "福利",
    "红包", "烟花", "春晚", "团圆", "拜年", "春节快乐",
]

# 消极词汇
NEGATIVE_WORDS = [
    "死亡", "事故", "爆炸", "坠毁", "地震", "洪水", "暴雨", "台风", "火灾", "失踪",
    "被捕", "逮捕", "犯罪", "诈骗", "骗局", "造假", "腐败", "丑闻", "崩盘", "暴跌",
    "倒闭", "裁员", "失业", "罢工", "抗议", "冲突", "战争", "制裁", "暴力", "悲剧",
    "去世", "离世", "遇难", "坠落", "泄漏", "污染", "投案", "举报", "通缉", "判刑",
    "批评", "愤怒", "痛心", "悲痛", "质疑", "争议", "道歉", "处罚", "罚款", "召回",
    "塌方", "崩塌", "侵权", "违规", "违法", "恶性",
]


def analyze_sentiment(title: str) -> tuple[str, float]:
    """
    分析标题情感
    返回: (sentiment_label, sentiment_score)
    - sentiment_label: "positive" / "neutral" / "negative"
    - sentiment_score: -1.0 ~ 1.0
    """
    pos_count = sum(1 for w in POSITIVE_WORDS if w in title)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in title)

    total = pos_count + neg_count
    if total == 0:
        return "neutral", 0.0

    score = (pos_count - neg_count) / total
    if score > 0.2:
        return "positive", round(min(score, 1.0), 2)
    elif score < -0.2:
        return "negative", round(max(score, -1.0), 2)
    else:
        return "neutral", round(score, 2)
