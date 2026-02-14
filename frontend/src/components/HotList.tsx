import React from 'react';
import { Table, Tag, Typography } from 'antd';
import type { HotTopic } from '../types';
import { PLATFORM_LABELS, PLATFORM_COLORS } from '../types';

const { Link } = Typography;

interface Props {
  data: HotTopic[];
  loading: boolean;
}

const columns = [
  {
    title: '排名',
    dataIndex: 'rank',
    key: 'rank',
    width: 70,
    render: (rank: number) => (
      <span style={{ fontWeight: rank <= 3 ? 'bold' : 'normal', color: rank <= 3 ? '#f5222d' : undefined }}>
        {rank}
      </span>
    ),
  },
  {
    title: '平台',
    dataIndex: 'platform',
    key: 'platform',
    width: 80,
    render: (p: string) => (
      <Tag color={PLATFORM_COLORS[p]}>{PLATFORM_LABELS[p] || p}</Tag>
    ),
  },
  {
    title: '热搜标题',
    dataIndex: 'title',
    key: 'title',
    render: (title: string, record: HotTopic) => (
      <span>
        {record.url ? <Link href={record.url} target="_blank">{title}</Link> : title}
        {record.is_cny_related && <Tag color="red" style={{ marginLeft: 8 }}>🧧春节</Tag>}
      </span>
    ),
  },
  {
    title: '热度',
    dataIndex: 'hot_value',
    key: 'hot_value',
    width: 120,
    render: (v: number | null) => (v != null ? v.toLocaleString() : '-'),
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    width: 100,
    render: (c: string | null) => c || '-',
  },
  {
    title: '情感',
    dataIndex: 'sentiment',
    key: 'sentiment',
    width: 70,
    render: (s: string | null) => {
      if (!s) return '-';
      const map: Record<string, { emoji: string; color: string }> = {
        positive: { emoji: '😊', color: '#52c41a' },
        neutral: { emoji: '😐', color: '#faad14' },
        negative: { emoji: '😟', color: '#f5222d' },
      };
      const cfg = map[s] || { emoji: '❓', color: '#999' };
      return <span style={{ color: cfg.color }}>{cfg.emoji}</span>;
    },
  },
];

const HotList: React.FC<Props> = ({ data, loading }) => {
  return (
    <Table
      columns={columns}
      dataSource={data}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 20 }}
      size="middle"
      scroll={{ x: 800 }}
    />
  );
};

export default HotList;
