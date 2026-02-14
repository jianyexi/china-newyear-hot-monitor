import React, { useState, useEffect } from 'react';
import { Card, Spin, Alert } from 'antd';
import ReactECharts from 'echarts-for-react';
import { api } from '../services/api';
import type { WordCloudItem } from '../types';

const WordCloudPanel: React.FC = () => {
  const [data, setData] = useState<WordCloudItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getWordCloud(24).then(setData).catch(() => setData([])).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;
  if (data.length === 0) return <Alert message="暂无词云数据" type="info" />;

  // Use scatter chart to visualize word frequency (since echarts-wordcloud may not be installed)
  const maxVal = Math.max(...data.map(d => d.value));
  const colors = ['#c41d2a', '#e6162d', '#ff4d4f', '#ff7a45', '#ffa940', '#fadb14', '#52c41a', '#1890ff', '#722ed1', '#eb2f96'];

  const option = {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.data[2]}: ${p.data[3]}次` },
    xAxis: { show: false, min: 0, max: 100 },
    yAxis: { show: false, min: 0, max: 100 },
    series: [{
      type: 'scatter',
      symbolSize: (val: number[]) => Math.max(12, (val[3] / maxVal) * 80),
      data: data.slice(0, 80).map((d, i) => [
        10 + Math.random() * 80,
        10 + Math.random() * 80,
        d.name,
        d.value,
      ]),
      label: {
        show: true,
        formatter: (p: any) => p.data[2],
        fontSize: (p: any) => Math.max(10, (p.data?.[3] / maxVal) * 28) || 12,
        color: () => colors[Math.floor(Math.random() * colors.length)],
        fontWeight: 'bold',
      },
      itemStyle: { opacity: 0 },
    }],
  };

  return (
    <Card title="☁️ 热词云图" extra={`共 ${data.length} 个热词`}>
      <ReactECharts option={option} style={{ height: 500 }} />
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
        {data.slice(0, 30).map((d, i) => (
          <span key={i} style={{
            padding: '4px 12px',
            borderRadius: 16,
            background: i < 3 ? '#fff1f0' : i < 10 ? '#fff7e6' : '#f6ffed',
            color: i < 3 ? '#cf1322' : i < 10 ? '#d48806' : '#389e0d',
            fontSize: Math.max(12, 20 - i * 0.3),
            fontWeight: i < 5 ? 'bold' : 'normal',
          }}>
            {d.name} ({d.value})
          </span>
        ))}
      </div>
    </Card>
  );
};

export default WordCloudPanel;
