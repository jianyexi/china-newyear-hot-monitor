import React, { useState } from 'react';
import { Card, Input, Spin, Empty } from 'antd';
import ReactECharts from 'echarts-for-react';
import { api } from '../services/api';
import type { TrendItem } from '../types';
import { PLATFORM_COLORS, PLATFORM_LABELS } from '../types';

const { Search } = Input;

const TrendChart: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [trends, setTrends] = useState<TrendItem[]>([]);

  const handleSearch = async (keyword: string) => {
    if (!keyword.trim()) return;
    setLoading(true);
    try {
      const data = await api.getTrends(keyword);
      setTrends(data);
    } catch {
      setTrends([]);
    } finally {
      setLoading(false);
    }
  };

  const getOption = () => ({
    title: { text: '热度趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: {
      data: trends.map((t) => `${PLATFORM_LABELS[t.platform] || t.platform} - ${t.title}`),
      bottom: 0,
    },
    xAxis: {
      type: 'time',
    },
    yAxis: { type: 'value', name: '热度' },
    series: trends.map((t) => ({
      name: `${PLATFORM_LABELS[t.platform] || t.platform} - ${t.title}`,
      type: 'line',
      smooth: true,
      data: t.timestamps.map((ts, i) => [ts, t.hot_values[i]]),
      itemStyle: { color: PLATFORM_COLORS[t.platform] },
    })),
  });

  return (
    <Card title="📈 趋势分析">
      <Search
        placeholder="输入关键词查看趋势，如：春晚、红包"
        enterButton="搜索"
        onSearch={handleSearch}
        style={{ marginBottom: 16 }}
      />
      {loading ? (
        <Spin style={{ display: 'block', textAlign: 'center', padding: 40 }} />
      ) : trends.length > 0 ? (
        <ReactECharts option={getOption()} style={{ height: 400 }} />
      ) : (
        <Empty description="输入关键词搜索趋势" />
      )}
    </Card>
  );
};

export default TrendChart;
