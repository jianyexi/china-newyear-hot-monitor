import React, { useState, useEffect } from 'react';
import { Card, List, Tag, Typography, Spin, Alert, Button, message } from 'antd';
import { FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import type { DailyReportItem } from '../types';

const { Text, Paragraph, Title } = Typography;

const ReportsPanel: React.FC = () => {
  const [reports, setReports] = useState<DailyReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<DailyReportItem | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.getReports().then(setReports).catch(() => setReports([])).finally(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateReport();
      message.success('报告已生成');
      const updated = await api.getReports();
      setReports(updated);
    } catch {
      message.error('生成失败，可能当天无数据');
    } finally {
      setGenerating(false);
    }
  };

  const handleView = async (date: string) => {
    try {
      const report = await api.getReport(date);
      setSelectedReport(report);
    } catch {
      message.error('加载报告失败');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card
        title={<span><FileTextOutlined /> 每日报告</span>}
        extra={
          <Button type="primary" icon={<PlusOutlined />} loading={generating} onClick={handleGenerate}>
            生成今日报告
          </Button>
        }
      >
        {reports.length > 0 ? (
          <List
            dataSource={reports}
            renderItem={(r) => (
              <List.Item
                actions={[
                  <Button type="link" onClick={() => handleView(r.report_date)}>查看</Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <span>
                      📊 {r.report_date}
                      <Tag color="blue" style={{ marginLeft: 8 }}>{r.report_type}</Tag>
                      <Tag>{r.total_topics} 话题</Tag>
                    </span>
                  }
                  description={`生成时间: ${new Date(r.created_at).toLocaleString('zh-CN')}`}
                />
              </List.Item>
            )}
          />
        ) : (
          <Alert message="暂无报告，点击右上角按钮生成" type="info" />
        )}
      </Card>

      {selectedReport && selectedReport.summary && (
        <Card
          title={`📋 ${selectedReport.report_date} 日报详情`}
          extra={<Button onClick={() => setSelectedReport(null)}>关闭</Button>}
          style={{ borderColor: '#1890ff' }}
        >
          <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontFamily: 'inherit' }}>
            {selectedReport.summary}
          </Paragraph>
        </Card>
      )}
    </div>
  );
};

export default ReportsPanel;
