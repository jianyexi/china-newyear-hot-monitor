import React from 'react';
import { Tabs } from 'antd';
import type { PlatformType } from '../types';
import { PLATFORM_LABELS } from '../types';

interface Props {
  active: PlatformType;
  onChange: (key: PlatformType) => void;
}

const platforms: { key: PlatformType; label: string }[] = [
  { key: 'all', label: '🔥 全部' },
  { key: 'weibo', label: `📱 ${PLATFORM_LABELS.weibo}` },
  { key: 'zhihu', label: `💬 ${PLATFORM_LABELS.zhihu}` },
  { key: 'baidu', label: `🔍 ${PLATFORM_LABELS.baidu}` },
  { key: 'douyin', label: `🎵 ${PLATFORM_LABELS.douyin}` },
  { key: 'xiaohongshu', label: `📕 ${PLATFORM_LABELS.xiaohongshu}` },
];

const PlatformTabs: React.FC<Props> = ({ active, onChange }) => {
  return (
    <Tabs
      activeKey={active}
      onChange={(key) => onChange(key as PlatformType)}
      items={platforms.map((p) => ({ key: p.key, label: p.label }))}
      size="large"
    />
  );
};

export default PlatformTabs;
