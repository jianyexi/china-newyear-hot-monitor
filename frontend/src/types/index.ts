export interface HotTopic {
  id: number;
  platform: string;
  title: string;
  url: string | null;
  rank: number;
  hot_value: number | null;
  category: string | null;
  is_cny_related: boolean;
  fetched_at: string;
}

export interface TrendItem {
  title: string;
  platform: string;
  hot_values: number[];
  timestamps: string[];
}

export interface PlatformStats {
  platform: string;
  total_topics: number;
  cny_related: number;
  latest_fetch: string | null;
}

export type PlatformType = 'all' | 'weibo' | 'zhihu' | 'baidu' | 'douyin';

export const PLATFORM_LABELS: Record<string, string> = {
  weibo: '微博',
  zhihu: '知乎',
  baidu: '百度',
  douyin: '抖音',
};

export const PLATFORM_COLORS: Record<string, string> = {
  weibo: '#E6162D',
  zhihu: '#0066FF',
  baidu: '#2932E1',
  douyin: '#000000',
};
