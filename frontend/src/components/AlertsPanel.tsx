import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Switch, Tag, Space,
  message, Spin, Typography, Popconfirm,
} from 'antd';
import { PlusOutlined, DeleteOutlined, BellOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import type { AlertRule } from '../types';

const { Text } = Typography;
const { TextArea } = Input;

const RULE_TYPES = [
  { value: 'spike', label: '🔥 热度突增', desc: '检测热度突然增长的话题' },
  { value: 'keyword', label: '🔔 关键词匹配', desc: '匹配指定关键词的话题' },
  { value: 'failure', label: '⚠️ 爬虫故障', desc: '爬虫抓取失败时告警' },
];

const AlertsPanel: React.FC = () => {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadRules = () => {
    setLoading(true);
    api.getAlerts().then(setRules).catch(() => setRules([])).finally(() => setLoading(false));
  };

  useEffect(() => { loadRules(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      if (values.config_json) {
        JSON.parse(values.config_json); // validate JSON
      }
      await api.createAlert(values);
      message.success('告警规则已创建');
      setModalOpen(false);
      form.resetFields();
      loadRules();
    } catch (e: any) {
      if (e.errorFields) return; // form validation
      message.error('创建失败：' + (e.message || '请检查配置'));
    }
  };

  const handleDelete = async (id: number) => {
    await api.deleteAlert(id);
    message.success('已删除');
    loadRules();
  };

  const columns = [
    {
      title: '状态', dataIndex: 'enabled', key: 'enabled', width: 70,
      render: (v: boolean) => v ? <Tag color="green">启用</Tag> : <Tag>禁用</Tag>,
    },
    {
      title: '类型', dataIndex: 'rule_type', key: 'rule_type', width: 120,
      render: (v: string) => RULE_TYPES.find(r => r.value === v)?.label || v,
    },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: 'Webhook', dataIndex: 'webhook_url', key: 'webhook_url', ellipsis: true,
      render: (v: string | null) => v ? <Text copyable={{ text: v }}>{v.slice(0, 40)}...</Text> : '-',
    },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: any, r: AlertRule) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id!)}>
          <Button type="link" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Card
      title={<span><BellOutlined /> 告警规则管理</span>}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新建规则
        </Button>
      }
    >
      {loading ? (
        <Spin style={{ display: 'block', margin: '40px auto' }} />
      ) : (
        <Table dataSource={rules} columns={columns} rowKey="id" pagination={false} size="small" />
      )}

      <Modal
        title="新建告警规则"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        okText="创建"
      >
        <Form form={form} layout="vertical" initialValues={{ enabled: true, rule_type: 'spike' }}>
          <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
            <Input placeholder="如：热度突增告警" />
          </Form.Item>
          <Form.Item name="rule_type" label="规则类型" rules={[{ required: true }]}>
            <Select options={RULE_TYPES.map(r => ({ ...r, label: `${r.label} — ${r.desc}` }))} />
          </Form.Item>
          <Form.Item name="config_json" label="规则配置 (JSON)" help='如: {"threshold": 2.0} 或 {"keywords": ["地震", "暴雨"]}'>
            <TextArea rows={3} placeholder='{"threshold": 2.0}' />
          </Form.Item>
          <Form.Item name="webhook_url" label="Webhook URL" help="支持企业微信/钉钉/自定义 Webhook">
            <Input placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch checkedChildren="开" unCheckedChildren="关" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default AlertsPanel;
