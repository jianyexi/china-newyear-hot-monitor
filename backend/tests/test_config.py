"""测试配置管理"""

import pytest
from app.config import get_runtime_config, update_runtime_config, _runtime_overrides


class TestConfig:
    def setup_method(self):
        _runtime_overrides.clear()

    def test_default_config(self):
        config = get_runtime_config()
        assert config["scrape_interval_minutes"] == 30
        assert config["scrape_top_n"] == 50
        assert "weibo" in config["enabled_platforms"]

    def test_update_interval(self):
        result = update_runtime_config({"scrape_interval_minutes": 15})
        assert result["scrape_interval_minutes"] == 15

    def test_update_platforms(self):
        result = update_runtime_config({"enabled_platforms": ["weibo", "baidu"]})
        assert result["enabled_platforms"] == ["weibo", "baidu"]

    def test_invalid_platform(self):
        with pytest.raises(ValueError, match="无效平台"):
            update_runtime_config({"enabled_platforms": ["invalid_platform"]})

    def test_empty_platforms(self):
        with pytest.raises(ValueError, match="至少启用一个"):
            update_runtime_config({"enabled_platforms": []})

    def test_interval_too_low(self):
        with pytest.raises(Exception):
            update_runtime_config({"scrape_interval_minutes": 1})

    def test_interval_too_high(self):
        with pytest.raises(Exception):
            update_runtime_config({"scrape_interval_minutes": 10000})

    def teardown_method(self):
        _runtime_overrides.clear()
