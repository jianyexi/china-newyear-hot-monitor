import type { HotTopic, TrendItem, PlatformStats, AnalysisReport } from '../types';

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
};
