export interface HotTopic {
  id: number;
  platform: string;
  title: string;
  url: string | null;
  rank: number;
  hot_value: number | null;
  category: string | null;
  is_cny_related: boolean;
  sentiment: string | null;
  sentiment_score: number | null;
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
  sentiment_summary: {
    positive: number;
    neutral: number;
    negative: number;
  } | null;
  ai_analysis: string | null;
}

export interface SearchResult {
  total: number;
  page: number;
  page_size: number;
  items: HotTopic[];
}

export interface TopicLifecycle {
  id: number;
  platform: string;
  title: string;
  first_seen: string;
  last_seen: string;
  peak_time: string | null;
  peak_rank: number | null;
  peak_hot_value: number | null;
  appearances: number;
  status: string;
}

export interface DailyReportItem {
  id: number;
  report_date: string;
  report_type: string;
  total_topics: number;
  summary: string | null;
  created_at: string;
}

export interface AlertRule {
  id?: number;
  name: string;
  rule_type: string;
  config_json: string | null;
  webhook_url: string | null;
  enabled: boolean;
  created_at?: string;
}

export interface CompareResult {
  period1: string;
  period2: string;
  new_topics: string[];
  dropped_topics: string[];
  rising_topics: Array<{ title: string; rank_before: number; rank_after: number; change: number }>;
  falling_topics: Array<{ title: string; rank_before: number; rank_after: number; change: number }>;
  common_count: number;
}

export interface SentimentStats {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  details: Array<{
    title: string;
    platform: string;
    sentiment: string;
    score: number;
    rank: number;
  }>;
}

export interface WordCloudItem {
  name: string;
  value: number;
}
