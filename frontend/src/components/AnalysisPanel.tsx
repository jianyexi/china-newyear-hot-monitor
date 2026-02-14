import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Tag, Typography, Spin, Collapse, Progress, List, Alert } from 'antd';
import { BarChartOutlined, GlobalOutlined, TagsOutlined, FireOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { api } from '../services/api';
import type { AnalysisReport } from '../types';
import { PLATFORM_LABELS } from '../types';

const { Title, Text, Paragraph } = Typography;

const AnalysisPanel: React.FC = () => {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalysis().then(setReport).catch(() => setReport(null)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;
  if (!report || report.total_topics === 0) return <Alert message="暂无数据" type="info" />;

  const categoryChartOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: report.categories.map(c => ({ name: c.category, value: c.count })),
    }],
  };

  const cnySubThemeOption = report.cny_summary?.sub_themes ? {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: Object.keys(report.cny_summary.sub_themes),
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: 'value', name: '话题数' },
    series: [{
      type: 'bar',
      data: Object.values(report.cny_summary.sub_themes).map(v => v.length),
      itemStyle: { color: '#cf1322', borderRadius: [4, 4, 0, 0] },
    }],
  } : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* AI 深度分析 */}
      {report.ai_analysis && (
        <Card title={<span>🤖 AI 深度分析</span>} style={{ borderColor: '#722ed1' }}>
          <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
            {report.ai_analysis}
          </Paragraph>
        </Card>
      )}

      <Row gutter={[16, 16]}>
        {/* 分类分布 */}
        <Col xs={24} lg={12}>
          <Card title={<span><TagsOutlined /> 话题分类分布</span>}>
            <ReactECharts option={categoryChartOption} style={{ height: 300 }} />
            <Collapse ghost items={report.categories.map((c, i) => ({
              key: i,
              label: (
                <span>
                  {c.category} <Tag>{c.count}条</Tag>
                  <Progress percent={c.percentage} size="small" style={{ width: 100, display: 'inline-block', marginLeft: 8 }} />
                </span>
              ),
              children: (
                <List
                  size="small"
                  dataSource={c.top_topics}
                  renderItem={(t) => <List.Item>{t}</List.Item>}
                />
              ),
            }))} />
          </Card>
        </Col>

        {/* 跨平台热点 */}
        <Col xs={24} lg={12}>
          <Card title={<span><GlobalOutlined /> 跨平台共同热点</span>}>
            {report.cross_platform_hot.length > 0 ? (
              <List
                dataSource={report.cross_platform_hot}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <span>
                          <FireOutlined style={{ color: '#f5222d' }} />{' '}
                          {Object.values(item.titles)[0]}
                        </span>
                      }
                      description={
                        <span>
                          出现在{' '}
                          {item.platforms.map(p => (
                            <Tag key={p} color="blue">{PLATFORM_LABELS[p] || p}</Tag>
                          ))}
                        </span>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Text type="secondary">当前无跨平台共同热点</Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 春节专题 */}
        <Col xs={24} lg={12}>
          <Card
            title={<span>🧧 春节专题分析</span>}
            style={{ borderColor: '#cf1322' }}
            extra={
              <span>
                <Tag color="red">{report.cny_summary?.count || 0}条</Tag>
                占比 {((report.cny_summary?.ratio || 0) * 100).toFixed(1)}%
              </span>
            }
          >
            {cnySubThemeOption && (
              <ReactECharts option={cnySubThemeOption} style={{ height: 250 }} />
            )}
            {report.cny_summary?.sub_themes && (
              <Collapse ghost items={Object.entries(report.cny_summary.sub_themes).map(([theme, topics], i) => ({
                key: i,
                label: <span>{theme} <Tag>{topics.length}条</Tag></span>,
                children: (
                  <List
                    size="small"
                    dataSource={topics}
                    renderItem={(t) => <List.Item>{t}</List.Item>}
                  />
                ),
              }))} />
            )}
          </Card>
        </Col>

        {/* 各平台独家视角 */}
        <Col xs={24} lg={12}>
          <Card title={<span><BarChartOutlined /> 各平台独家视角</span>}>
            <Collapse
              ghost
              items={report.platform_insights.map((p, i) => ({
                key: i,
                label: (
                  <span>
                    {PLATFORM_LABELS[p.platform] || p.platform}{' '}
                    <Tag color={p.cny_ratio > 0.2 ? 'red' : 'default'}>
                      春节占比 {(p.cny_ratio * 100).toFixed(0)}%
                    </Tag>
                  </span>
                ),
                children: (
                  <div>
                    <Title level={5}>🔝 热门话题</Title>
                    <List size="small" dataSource={p.top_topics} renderItem={(t) => <List.Item>{t}</List.Item>} />
                    {p.unique_topics.length > 0 && (
                      <>
                        <Title level={5}>💎 独家话题</Title>
                        <List size="small" dataSource={p.unique_topics} renderItem={(t) => <List.Item>{t}</List.Item>} />
                      </>
                    )}
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AnalysisPanel;
