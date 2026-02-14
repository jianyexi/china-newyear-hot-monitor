import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Spin, Alert, Segmented, Typography } from 'antd';
import { ClockCircleOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import type { TopicLifecycle } from '../types';
import { PLATFORM_LABELS, PLATFORM_COLORS } from '../types';

const { Text } = Typography;

const STATUS_CONFIG: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
  rising: { color: '#52c41a', label: '🔼 上升', icon: <RiseOutlined /> },
  peak: { color: '#f5222d', label: '🔥 巅峰', icon: <RiseOutlined /> },
  falling: { color: '#faad14', label: '🔽 下降', icon: <FallOutlined /> },
  off: { color: '#d9d9d9', label: '⏹ 下榜', icon: <ClockCircleOutlined /> },
};

const LifecyclePanel: React.FC = () => {
  const [data, setData] = useState<TopicLifecycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    api.getLifecycle(status || undefined)
      .then(setData).catch(() => setData([])).finally(() => setLoading(false));
  }, [status]);

  const columns = [
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => {
        const cfg = STATUS_CONFIG[s] || { color: '#999', label: s };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '平台', dataIndex: 'platform', key: 'platform', width: 80,
      render: (p: string) => <Tag color={PLATFORM_COLORS[p]}>{PLATFORM_LABELS[p] || p}</Tag>,
    },
    { title: '话题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '出现次数', dataIndex: 'appearances', key: 'appearances', width: 90 },
    {
      title: '最高排名', dataIndex: 'peak_rank', key: 'peak_rank', width: 90,
      render: (v: number | null) => v ? `#${v}` : '-',
    },
    {
      title: '首次出现', dataIndex: 'first_seen', key: 'first_seen', width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '最后出现', dataIndex: 'last_seen', key: 'last_seen', width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
  ];

  return (
    <Card
      title="📊 话题生命周期"
      extra={
        <Segmented
          value={status}
          onChange={(v) => setStatus(v as string)}
          options={[
            { label: '全部', value: '' },
            { label: '🔼 上升', value: 'rising' },
            { label: '🔥 巅峰', value: 'peak' },
            { label: '🔽 下降', value: 'falling' },
            { label: '⏹ 下榜', value: 'off' },
          ]}
        />
      }
    >
      {loading ? (
        <Spin style={{ display: 'block', margin: '40px auto' }} />
      ) : data.length > 0 ? (
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 15 }}
          size="small"
          scroll={{ x: 900 }}
        />
      ) : (
        <Alert message="暂无生命周期数据" type="info" />
      )}
    </Card>
  );
};

export default LifecyclePanel;
