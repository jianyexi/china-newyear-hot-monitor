import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Tag, Typography, Spin, Alert } from 'antd';
import { SmileOutlined, MehOutlined, FrownOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { api } from '../services/api';
import type { SentimentStats } from '../types';
import { PLATFORM_LABELS } from '../types';

const { Text } = Typography;

const SENTIMENT_COLORS = { positive: '#52c41a', neutral: '#faad14', negative: '#f5222d' };
const SENTIMENT_LABELS = { positive: '😊 正面', neutral: '😐 中性', negative: '😟 负面' };
const SENTIMENT_ICONS = { positive: <SmileOutlined />, neutral: <MehOutlined />, negative: <FrownOutlined /> };

const SentimentPanel: React.FC = () => {
  const [data, setData] = useState<SentimentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSentiment().then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;
  if (!data || data.total === 0) return <Alert message="暂无情感分析数据" type="info" />;

  const pieOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      data: [
        { name: '正面', value: data.positive, itemStyle: { color: SENTIMENT_COLORS.positive } },
        { name: '中性', value: data.neutral, itemStyle: { color: SENTIMENT_COLORS.neutral } },
        { name: '负面', value: data.negative, itemStyle: { color: SENTIMENT_COLORS.negative } },
      ],
    }],
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Row gutter={[16, 16]}>
        {(['positive', 'neutral', 'negative'] as const).map(key => (
          <Col xs={8} key={key}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, color: SENTIMENT_COLORS[key] }}>
                  {SENTIMENT_ICONS[key]}
                </div>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: SENTIMENT_COLORS[key] }}>
                  {data[key]}
                </div>
                <Text type="secondary">{SENTIMENT_LABELS[key]}</Text>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="情感分布">
            <ReactECharts option={pieOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="情感最强话题 Top 20">
            {data.details.map((d, i) => (
              <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Tag color={SENTIMENT_COLORS[d.sentiment as keyof typeof SENTIMENT_COLORS] || '#666'}>
                  {d.sentiment === 'positive' ? '😊' : d.sentiment === 'negative' ? '😟' : '😐'}
                </Tag>
                <Tag>{PLATFORM_LABELS[d.platform] || d.platform}</Tag>
                <Text ellipsis style={{ flex: 1 }}>{d.title}</Text>
                <Text type="secondary" style={{ whiteSpace: 'nowrap' }}>
                  {d.score > 0 ? '+' : ''}{d.score.toFixed(2)}
                </Text>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SentimentPanel;
