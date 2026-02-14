import type {
  HotTopic, TrendItem, PlatformStats, AnalysisReport,
  SearchResult, TopicLifecycle, DailyReportItem, AlertRule,
  CompareResult, SentimentStats, WordCloudItem,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

async function request<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getTopics(platform?: string, cnyOnly = false) {
    const params: Record<string, string> = {};
    if (platform && platform !== 'all') params.platform = platform;
    if (cnyOnly) params.cny_only = 'true';
    return request<HotTopic[]>('/topics', params);
  },

  getHistory(platform?: string, hours = 24) {
    const params: Record<string, string> = { hours: String(hours) };
    if (platform && platform !== 'all') params.platform = platform;
    return request<HotTopic[]>('/topics/history', params);
  },

  getTrends(title: string, hours = 24) {
    return request<TrendItem[]>('/trends', { title, hours: String(hours) });
  },

  getStats() {
    return request<PlatformStats[]>('/stats');
  },

  getAnalysis() {
    return request<AnalysisReport>('/analysis');
  },

  getConfig() {
    return request<Record<string, unknown>>('/config');
  },

  updateConfig(updates: Record<string, unknown>) {
    return fetch(`${API_BASE}/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    }).then(r => r.json());
  },

  triggerScrape() {
    return fetch(`${API_BASE}/scrape`, { method: 'POST' }).then(r => r.json());
  },

  getAvailablePlatforms() {
    return request<{ available: Array<{ id: string; name: string; icon: string }>; enabled: string[] }>('/config/platforms');
  },

  exportCsv(platform?: string, hours = 24) {
    const params = new URLSearchParams({ hours: String(hours) });
    if (platform && platform !== 'all') params.set('platform', platform);
    window.open(`${API_BASE}/export/csv?${params}`, '_blank');
  },

  // ---- 新增 API ----

  search(keyword: string, platform?: string, hours = 24, page = 1, pageSize = 20) {
    const params: Record<string, string> = { keyword, hours: String(hours), page: String(page), page_size: String(pageSize) };
    if (platform && platform !== 'all') params.platform = platform;
    return request<SearchResult>('/search', params);
  },

  getLifecycle(status?: string, platform?: string, limit = 50) {
    const params: Record<string, string> = { limit: String(limit) };
    if (status) params.status = status;
    if (platform && platform !== 'all') params.platform = platform;
    return request<TopicLifecycle[]>('/lifecycle', params);
  },

  getReports(type = 'daily', limit = 30) {
    return request<DailyReportItem[]>('/reports', { report_type: type, limit: String(limit) });
  },

  getReport(date: string) {
    return request<DailyReportItem>(`/reports/${date}`);
  },

  generateReport(date?: string) {
    const params: Record<string, string> = {};
    if (date) params.report_date = date;
    return fetch(`${API_BASE}/reports/generate?${new URLSearchParams(params)}`, { method: 'POST' }).then(r => r.json());
  },

  getAlerts() {
    return request<AlertRule[]>('/alerts');
  },

  createAlert(rule: Omit<AlertRule, 'id' | 'created_at'>) {
    return fetch(`${API_BASE}/alerts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rule),
    }).then(r => r.json());
  },

  deleteAlert(id: number) {
    return fetch(`${API_BASE}/alerts/${id}`, { method: 'DELETE' }).then(r => r.json());
  },

  compare(hoursAgo1 = 0, hoursAgo2 = 24, platform?: string) {
    const params: Record<string, string> = { hours_ago_1: String(hoursAgo1), hours_ago_2: String(hoursAgo2) };
    if (platform && platform !== 'all') params.platform = platform;
    return request<CompareResult>('/compare', params);
  },

  getWordCloud(hours = 24, platform?: string) {
    const params: Record<string, string> = { hours: String(hours) };
    if (platform && platform !== 'all') params.platform = platform;
    return request<WordCloudItem[]>('/wordcloud', params);
  },

  getSentiment(platform?: string) {
    const params: Record<string, string> = {};
    if (platform && platform !== 'all') params.platform = platform;
    return request<SentimentStats>('/sentiment', params);
  },

  getWsUrl() {
    const base = API_BASE.replace(/\/api$/, '').replace('http', 'ws');
    return `${base}/ws`;
  },
};
