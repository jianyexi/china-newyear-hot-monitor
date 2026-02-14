"""测试去重工具"""

from app.dedup import make_dedup_key, title_similarity


class TestDedup:
    def test_dedup_key_deterministic(self):
        k1 = make_dedup_key("weibo", "春晚节目单曝光")
        k2 = make_dedup_key("weibo", "春晚节目单曝光")
        assert k1 == k2

    def test_dedup_key_platform_matters(self):
        k1 = make_dedup_key("weibo", "春晚节目单曝光")
        k2 = make_dedup_key("zhihu", "春晚节目单曝光")
        assert k1 != k2

    def test_dedup_key_ignores_punctuation(self):
        k1 = make_dedup_key("weibo", "春晚节目单曝光！")
        k2 = make_dedup_key("weibo", "春晚节目单曝光")
        assert k1 == k2

    def test_similarity_identical(self):
        assert title_similarity("春晚节目单曝光", "春晚节目单曝光") == 1.0

    def test_similarity_related(self):
        sim = title_similarity("春晚节目单曝光了", "2025春晚节目单")
        assert sim > 0.3

    def test_similarity_unrelated(self):
        sim = title_similarity("人工智能芯片", "春晚节目单曝光")
        assert sim < 0.3
