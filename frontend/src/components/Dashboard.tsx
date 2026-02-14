import React, { useEffect, useState, useCallback } from 'react';
import { Layout, Row, Col, Card, Statistic, Switch, Typography, Space, message, Tabs, Button } from 'antd';
import { FireOutlined, RocketOutlined, BarChartOutlined, UnorderedListOutlined, SettingOutlined, DownloadOutlined } from '@ant-design/icons';
import PlatformTabs from './PlatformTabs';
import HotList from './HotList';
import TrendChart from './TrendChart';
import AnalysisPanel from './AnalysisPanel';
import SettingsPanel from './SettingsPanel';
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

  const loadData = useCallback(async () => {
    setLoading(true);
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
      <Header style={{ background: '#c41d2a', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          🧧 中国过年热点舆论监控平台
        </Title>
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
                <>
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
                </>
              ),
            },
            {
              key: 'analysis',
              label: <span><BarChartOutlined /> 智能分析</span>,
              children: <AnalysisPanel />,
            },
            {
              key: 'settings',
              label: <span><SettingOutlined /> 系统设置</span>,
              children: <SettingsPanel />,
            },
          ]}
        />
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        中国过年热点舆论监控平台 ©{new Date().getFullYear()} | 数据每30分钟自动更新
      </Footer>
    </Layout>
  );
};

export default Dashboard;
