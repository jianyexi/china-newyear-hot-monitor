"""数据去重工具"""

import hashlib
import re


def make_dedup_key(platform: str, title: str) -> str:
    """生成去重 key: platform + 标题核心词 hash"""
    # 提取中文字符和字母数字，忽略标点
    core = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", title)
    raw = f"{platform}:{core}"
    return hashlib.md5(raw.encode()).hexdigest()


def title_similarity(t1: str, t2: str) -> float:
    """计算两个标题的相似度 (bigram overlap)"""
    def bigrams(s: str) -> set[str]:
        chars = re.findall(r"[\u4e00-\u9fff]", s)
        return {chars[i] + chars[i + 1] for i in range(len(chars) - 1)} if len(chars) > 1 else set()

    b1, b2 = bigrams(t1), bigrams(t2)
    if not b1 or not b2:
        return 0.0
    overlap = len(b1 & b2)
    return overlap / min(len(b1), len(b2))
