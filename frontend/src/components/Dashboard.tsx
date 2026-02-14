import React, { useEffect, useState, useCallback } from 'react';
import { Layout, Row, Col, Card, Statistic, Switch, Typography, Space, message, Tabs, Button, Badge, Tag } from 'antd';
import {
  FireOutlined, RocketOutlined, BarChartOutlined, UnorderedListOutlined,
  SettingOutlined, DownloadOutlined, SearchOutlined, SwapOutlined,
  HeartOutlined, ClockCircleOutlined, BellOutlined, FileTextOutlined,
  CloudOutlined, WifiOutlined,
} from '@ant-design/icons';
import PlatformTabs from './PlatformTabs';
import HotList from './HotList';
import TrendChart from './TrendChart';
import AnalysisPanel from './AnalysisPanel';
import SettingsPanel from './SettingsPanel';
import SentimentPanel from './SentimentPanel';
import ComparePanel from './ComparePanel';
import WordCloudPanel from './WordCloudPanel';
import LifecyclePanel from './LifecyclePanel';
import AlertsPanel from './AlertsPanel';
import ReportsPanel from './ReportsPanel';
import ErrorBoundary from './ErrorBoundary';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';
import type { HotTopic, PlatformType, PlatformStats } from '../types';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [platform, setPlatform] = useState<PlatformType>('all');
  const [cnyOnly, setCnyOnly] = useState(false);
  const [topics, setTopics] = useState<HotTopic[]>([]);
  const [stats, setStats] = useState<PlatformStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [newDataBadge, setNewDataBadge] = useState(false);

  const { connected } = useWebSocket((msg) => {
    if (msg.type === 'scrape_complete') {
      setNewDataBadge(true);
      message.info(`🔔 新数据已到达：${msg.total} 条话题`);
      loadData();
    }
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setNewDataBadge(false);
    try {
      const [topicData, statsData] = await Promise.all([
        api.getTopics(platform, cnyOnly),
        api.getStats(),
      ]);
      setTopics(topicData);
      setStats(statsData);
    } catch {
      message.error('数据加载失败，请检查后端服务');
    } finally {
      setLoading(false);
    }
  }, [platform, cnyOnly]);

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 60_000);
    return () => clearInterval(timer);
  }, [loadData]);

  const totalTopics = stats.reduce((s, i) => s + i.total_topics, 0);
  const totalCny = stats.reduce((s, i) => s + i.cny_related, 0);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#c41d2a', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px' }}>
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          🧧 中国过年热点舆论监控平台
        </Title>
        <Space>
          <Tag color={connected ? 'green' : 'red'} icon={<WifiOutlined />}>
            {connected ? '实时连接' : '离线'}
          </Tag>
          {newDataBadge && <Badge dot><Tag color="gold">新数据</Tag></Badge>}
        </Space>
      </Header>
      <Content style={{ padding: '24px', maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="监控平台" value={stats.length} prefix={<RocketOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="总话题数" value={totalTopics} prefix={<FireOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic title="春节相关" value={totalCny} prefix="🧧" valueStyle={{ color: '#cf1322' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Space direction="vertical">
                <span>仅看春节话题</span>
                <Switch checked={cnyOnly} onChange={setCnyOnly} checkedChildren="开" unCheckedChildren="关" />
              </Space>
            </Card>
          </Col>
        </Row>

        <Tabs
          defaultActiveKey="list"
          size="large"
          style={{ marginBottom: 16 }}
          items={[
            {
              key: 'list',
              label: <span><UnorderedListOutlined /> 热搜列表</span>,
              children: (
                <ErrorBoundary>
                  <Card style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <PlatformTabs active={platform} onChange={setPlatform} />
                      <Button icon={<DownloadOutlined />} onClick={() => api.exportCsv(platform)}>
                        导出 CSV
                      </Button>
                    </div>
                    <HotList data={topics} loading={loading} />
                  </Card>
                  <TrendChart />
                </ErrorBoundary>
              ),
            },
            {
              key: 'analysis',
              label: <span><BarChartOutlined /> 智能分析</span>,
              children: <ErrorBoundary><AnalysisPanel /></ErrorBoundary>,
            },
            {
              key: 'sentiment',
              label: <span><HeartOutlined /> 情感分析</span>,
              children: <ErrorBoundary><SentimentPanel /></ErrorBoundary>,
            },
            {
              key: 'compare',
              label: <span><SwapOutlined /> 对比分析</span>,
              children: <ErrorBoundary><ComparePanel /></ErrorBoundary>,
            },
            {
              key: 'wordcloud',
              label: <span><CloudOutlined /> 热词云</span>,
              children: <ErrorBoundary><WordCloudPanel /></ErrorBoundary>,
            },
            {
              key: 'lifecycle',
              label: <span><ClockCircleOutlined /> 生命周期</span>,
              children: <ErrorBoundary><LifecyclePanel /></ErrorBoundary>,
            },
            {
              key: 'reports',
              label: <span><FileTextOutlined /> 每日报告</span>,
              children: <ErrorBoundary><ReportsPanel /></ErrorBoundary>,
            },
            {
              key: 'alerts',
              label: <span><BellOutlined /> 告警管理</span>,
              children: <ErrorBoundary><AlertsPanel /></ErrorBoundary>,
            },
            {
              key: 'settings',
              label: <span><SettingOutlined /> 系统设置</span>,
              children: <ErrorBoundary><SettingsPanel /></ErrorBoundary>,
            },
          ]}
        />
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        中国过年热点舆论监控平台 v2.0 ©{new Date().getFullYear()} | 数据自动更新 | WebSocket {connected ? '✅' : '❌'}
      </Footer>
    </Layout>
  );
};

export default Dashboard;
