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

export type PlatformType = 'all' | 'weibo' | 'zhihu' | 'baidu' | 'douyin' | 'xiaohongshu';

export const PLATFORM_LABELS: Record<string, string> = {
  weibo: '微博',
  zhihu: '知乎',
  baidu: '百度',
  douyin: '抖音',
  xiaohongshu: '小红书',
};

export const PLATFORM_COLORS: Record<string, string> = {
  weibo: '#E6162D',
  zhihu: '#0066FF',
  baidu: '#2932E1',
  douyin: '#000000',
  xiaohongshu: '#FF2442',
};

export interface CategoryBreakdown {
  category: string;
  count: number;
  percentage: number;
  top_topics: string[];
}

export interface PlatformInsight {
  platform: string;
  top_topics: string[];
  cny_ratio: number;
  unique_topics: string[];
}

export interface AnalysisReport {
  generated_at: string;
  total_topics: number;
  platforms_covered: string[];
  categories: CategoryBreakdown[];
  cross_platform_hot: Array<{
    keyword: string;
    platforms: string[];
    titles: Record<string, string>;
    platform_count: number;
  }>;
  platform_insights: PlatformInsight[];
  cny_summary: {
    count: number;
    ratio: number;
    platforms: Record<string, number>;
    top_topics: string[];
    sub_themes: Record<string, string[]>;
  };
  ai_analysis: string | null;
}
