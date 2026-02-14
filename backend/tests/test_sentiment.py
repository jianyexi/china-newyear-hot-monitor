"""测试情感分析"""

from app.sentiment import analyze_sentiment


class TestSentiment:
    def test_positive(self):
        label, score = analyze_sentiment("中国队夺冠 全网点赞")
        assert label == "positive"
        assert score > 0

    def test_negative(self):
        label, score = analyze_sentiment("重大事故造成死亡")
        assert label == "negative"
        assert score < 0

    def test_neutral(self):
        label, score = analyze_sentiment("今天天气不错")
        assert label == "neutral"
        assert score == 0.0

    def test_mixed(self):
        label, score = analyze_sentiment("虽然有争议但最终成功")
        # Both positive and negative words, but positive wins
        assert label in ("positive", "neutral")
