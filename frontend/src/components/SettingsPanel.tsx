import React, { useEffect, useState } from 'react';
import {
  Card, Form, InputNumber, Switch, Select, Tag, Input, Button, Space,
  message, Divider, Typography, Row, Col, Tooltip, Spin,
} from 'antd';
import {
  SettingOutlined, ThunderboltOutlined, PlusOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { api } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PlatformInfo {
  id: string;
  name: string;
  icon: string;
}

const SettingsPanel: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [config, setConfig] = useState<Record<string, any>>({});
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [newCustomKw, setNewCustomKw] = useState('');

  useEffect(() => {
    Promise.all([api.getConfig(), api.getAvailablePlatforms()])
      .then(([cfg, plat]) => {
        setConfig(cfg);
        setPlatforms(plat.available);
      })
      .catch(() => message.error('加载配置失败'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (updates: Record<string, unknown>) => {
    setSaving(true);
    try {
      const res = await api.updateConfig(updates);
      setConfig(res.config);
      message.success('配置已保存');
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleScrape = async () => {
    setScraping(true);
    try {
      await api.triggerScrape();
      message.success('抓取任务已触发，稍后刷新查看');
    } catch {
      message.error('触发失败');
    } finally {
      setTimeout(() => setScraping(false), 3000);
    }
  };

  const addCnyKeyword = () => {
    if (!newKeyword.trim()) return;
    const updated = [...(config.cny_keywords || []), newKeyword.trim()];
    handleSave({ cny_keywords: [...new Set(updated)] });
    setNewKeyword('');
  };

  const removeCnyKeyword = (kw: string) => {
    handleSave({ cny_keywords: (config.cny_keywords || []).filter((k: string) => k !== kw) });
  };

  const addCustomKeyword = () => {
    if (!newCustomKw.trim()) return;
    const updated = [...(config.custom_keywords || []), newCustomKw.trim()];
    handleSave({ custom_keywords: [...new Set(updated)] });
    setNewCustomKw('');
  };

  const removeCustomKeyword = (kw: string) => {
    handleSave({ custom_keywords: (config.custom_keywords || []).filter((k: string) => k !== kw) });
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* 快捷操作 */}
      <Card>
        <Space size="large">
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={scraping}
            onClick={handleScrape}
            size="large"
          >
            立即抓取
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()} size="large">
            刷新页面
          </Button>
          <Text type="secondary">
            当前状态：已启用 {config.enabled_platforms?.length || 0} 个平台 | 
            每 {config.scrape_interval_minutes} 分钟自动抓取 | 
            每平台 Top {config.scrape_top_n}
          </Text>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        {/* 抓取配置 */}
        <Col xs={24} lg={12}>
          <Card title={<span><SettingOutlined /> 抓取配置</span>}>
            <Form layout="vertical">
              <Form.Item label="抓取间隔（分钟）" tooltip="多久自动抓取一次热搜">
                <InputNumber
                  min={5} max={1440} value={config.scrape_interval_minutes}
                  onChange={(v) => v && handleSave({ scrape_interval_minutes: v })}
                  style={{ width: '100%' }}
                  addonAfter="分钟"
                />
              </Form.Item>

              <Form.Item label="每平台抓取条数" tooltip="每个平台最多抓取多少条热搜">
                <InputNumber
                  min={10} max={100} value={config.scrape_top_n}
                  onChange={(v) => v && handleSave({ scrape_top_n: v })}
                  style={{ width: '100%' }}
                  addonAfter="条"
                />
              </Form.Item>

              <Form.Item label="启用平台" tooltip="选择要监控的平台">
                <Select
                  mode="multiple"
                  value={config.enabled_platforms}
                  onChange={(v) => handleSave({ enabled_platforms: v })}
                  style={{ width: '100%' }}
                  options={platforms.map(p => ({
                    label: `${p.icon} ${p.name}`,
                    value: p.id,
                  }))}
                />
              </Form.Item>

              <Form.Item label="智能分析">
                <Switch
                  checked={config.analysis_enabled}
                  onChange={(v) => handleSave({ analysis_enabled: v })}
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* AI 配置 */}
        <Col xs={24} lg={12}>
          <Card
            title={<span>🤖 AI 分析配置</span>}
            extra={config.openai_configured
              ? <Tag color="green">已配置 API Key</Tag>
              : <Tag color="orange">未配置（设置 OPENAI_API_KEY 环境变量）</Tag>
            }
          >
            <Form layout="vertical">
              <Form.Item label="AI 模型" tooltip="用于深度分析的 LLM 模型">
                <Select
                  value={config.openai_model}
                  onChange={(v) => handleSave({ openai_model: v })}
                  style={{ width: '100%' }}
                  options={[
                    { label: 'GPT-4o Mini (快速)', value: 'gpt-4o-mini' },
                    { label: 'GPT-4o (高质量)', value: 'gpt-4o' },
                    { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
                    { label: 'GPT-3.5 Turbo (经济)', value: 'gpt-3.5-turbo' },
                    { label: 'DeepSeek Chat', value: 'deepseek-chat' },
                    { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
                  ]}
                />
              </Form.Item>
              <Text type="secondary">
                💡 设置 <code>OPENAI_BASE_URL</code> 可切换到兼容 API（如 DeepSeek、Azure 等）
              </Text>
            </Form>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 春节关键词 */}
        <Col xs={24} lg={12}>
          <Card title="🧧 春节关键词" extra={<Tag>{(config.cny_keywords || []).length} 个</Tag>}>
            <div style={{ marginBottom: 12 }}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  placeholder="添加春节关键词"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onPressEnter={addCnyKeyword}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={addCnyKeyword}>添加</Button>
              </Space.Compact>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {(config.cny_keywords || []).map((kw: string) => (
                <Tag key={kw} closable onClose={() => removeCnyKeyword(kw)} color="red">{kw}</Tag>
              ))}
            </div>
          </Card>
        </Col>

        {/* 自定义监控关键词 */}
        <Col xs={24} lg={12}>
          <Card
            title="🔍 自定义监控关键词"
            extra={<Tag>{(config.custom_keywords || []).length} 个</Tag>}
          >
            <div style={{ marginBottom: 12 }}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  placeholder="添加自定义监控关键词（如：AI、教育）"
                  value={newCustomKw}
                  onChange={(e) => setNewCustomKw(e.target.value)}
                  onPressEnter={addCustomKeyword}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={addCustomKeyword}>添加</Button>
              </Space.Compact>
            </div>
            {(config.custom_keywords || []).length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {(config.custom_keywords || []).map((kw: string) => (
                  <Tag key={kw} closable onClose={() => removeCustomKeyword(kw)} color="blue">{kw}</Tag>
                ))}
              </div>
            ) : (
              <Text type="secondary">添加自定义关键词后，匹配的热搜也会被标记为相关话题</Text>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SettingsPanel;
