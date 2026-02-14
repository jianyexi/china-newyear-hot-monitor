import React, { useState, useEffect } from 'react';
import { Card, Spin, Alert, Segmented, Tag, Typography, Row, Col, Table } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, SwapOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import type { CompareResult } from '../types';

const { Text, Title } = Typography;

const ComparePanel: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<CompareResult | null>(null);
  const [period, setPeriod] = useState<number>(24);

  useEffect(() => {
    setLoading(true);
    api.compare(0, period).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [period]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;
  if (!data) return <Alert message="暂无对比数据" type="info" />;

  const risingColumns = [
    { title: '话题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '之前排名', dataIndex: 'rank_before', key: 'rank_before', width: 90 },
    { title: '当前排名', dataIndex: 'rank_after', key: 'rank_after', width: 90 },
    {
      title: '变化', dataIndex: 'change', key: 'change', width: 80,
      render: (v: number, r: any) => (
        <span style={{ color: r.rank_after < r.rank_before ? '#52c41a' : '#f5222d' }}>
          {r.rank_after < r.rank_before ? <ArrowUpOutlined /> : <ArrowDownOutlined />} {v}
        </span>
      ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <SwapOutlined style={{ fontSize: 20 }} />
          <Text>对比时段：当前 vs </Text>
          <Segmented
            value={period}
            onChange={(v) => setPeriod(v as number)}
            options={[
              { label: '1小时前', value: 1 },
              { label: '6小时前', value: 6 },
              { label: '24小时前', value: 24 },
              { label: '48小时前', value: 48 },
              { label: '72小时前', value: 72 },
            ]}
          />
          <Tag color="blue">共同话题: {data.common_count}</Tag>
        </div>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={<span style={{ color: '#52c41a' }}>🆕 新上榜 ({data.new_topics.length})</span>}>
            {data.new_topics.length > 0 ? (
              data.new_topics.map((t, i) => (
                <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <Tag color="green">{i + 1}</Tag> {t}
                </div>
              ))
            ) : (
              <Text type="secondary">无新上榜话题</Text>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<span style={{ color: '#f5222d' }}>📉 已下榜 ({data.dropped_topics.length})</span>}>
            {data.dropped_topics.length > 0 ? (
              data.dropped_topics.map((t, i) => (
                <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <Tag color="red">{i + 1}</Tag> {t}
                </div>
              ))
            ) : (
              <Text type="secondary">无下榜话题</Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={<span style={{ color: '#52c41a' }}><ArrowUpOutlined /> 排名上升</span>}>
            <Table
              dataSource={data.rising_topics}
              columns={risingColumns}
              rowKey="title"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<span style={{ color: '#f5222d' }}><ArrowDownOutlined /> 排名下降</span>}>
            <Table
              dataSource={data.falling_topics}
              columns={risingColumns}
              rowKey="title"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ComparePanel;
