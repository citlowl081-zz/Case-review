import React, { useState } from 'react';
import {
  Card,
  Select,
  Button,
  Typography,
  Tag,
  Table,
  Empty,
  message,
  Space,
  Spin,
  Descriptions,
} from 'antd';
import {
  AuditOutlined,
  PlayCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  FileSearchOutlined,
  ClockCircleOutlined,
  FileSyncOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const REVIEW_TYPES = [
  { value: 'visit_window', label: '访视时间窗审核', icon: <ClockCircleOutlined /> },
  { value: 'inclusion_exclusion', label: '纳排标准审核', icon: <FileSearchOutlined /> },
  { value: 'ae_logic', label: 'AE时间逻辑审核', icon: <WarningOutlined /> },
  { value: 'consistency', label: '文档一致性审核', icon: <FileSyncOutlined /> },
];

// Mock findings for demonstration
const MOCK_FINDINGS = [
  {
    review_type: 'visit_window',
    severity: '高' as const,
    description: 'V2 访视日期为 2026-06-15，方案要求 V2 应在 V1 后 14±2 天内完成。当前 V2 距 V1 为 19 天，超出访视窗口。',
    source_reference: '《研究方案》第5.2节 访视流程表',
    suggestion: '建议记录方案偏离，并补充说明原因。如为合理偏离，需研究者签字确认。',
  },
  {
    review_type: 'inclusion_exclusion',
    severity: '中' as const,
    description: '病例中记录受试者近30天内使用过全身糖皮质激素，方案排除标准规定筛选前14天内不得使用该类药物。',
    source_reference: '《研究方案》第4.1节 排除标准',
    suggestion: '请研究者确认用药时间、剂量和适应症，判断是否符合排除标准。如确认排除，应在筛选失败记录中注明。',
  },
  {
    review_type: 'ae_logic',
    severity: '中' as const,
    description: '病历中记录\"2026-06-01 出现咳嗽\"，但 AE 表中开始时间填写为 2026-06-03。存在 2 天时间差异。',
    source_reference: '《病例记录》第2页 / 《AE表》第3行',
    suggestion: '请核实 AE 实际发生时间，并统一病历与 AE 表记录。如病历记录有误，应在病历中更正并注明。',
  },
  {
    review_type: 'consistency',
    severity: '高' as const,
    description: '研究方案中规定试验药物保存温度为 2-8℃，但药物管理手册中写为 15-25℃。两处描述不一致。',
    source_reference: '《研究方案》第7.3节 / 《药物管理手册》第2章',
    suggestion: '请确认最终执行标准，并对药物管理手册进行修订。此差异可能影响中心执行和稽查判断。',
  },
];

const severityColor = (s: string) => {
  switch (s) {
    case '高': return 'red';
    case '中': return 'orange';
    case '低': return 'blue';
    default: return 'default';
  }
};

const reviewTypeLabel = (t: string) => {
  return REVIEW_TYPES.find((r) => r.value === t)?.label || t;
};

export default function Review() {
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    REVIEW_TYPES.map((r) => r.value)
  );
  const [reviewing, setReviewing] = useState(false);
  const [findings, setFindings] = useState<typeof MOCK_FINDINGS>([]);
  const [hasReviewed, setHasReviewed] = useState(false);

  const handleReview = async () => {
    if (selectedTypes.length === 0) {
      message.warning('请选择至少一种审核类型');
      return;
    }
    setReviewing(true);
    // Simulate review process — in production, this would call the backend API
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setFindings(MOCK_FINDINGS.filter((f) => selectedTypes.includes(f.review_type)));
    setHasReviewed(true);
    setReviewing(false);
    message.success('审核完成');
  };

  const columns = [
    {
      title: '审核类型',
      dataIndex: 'review_type',
      key: 'review_type',
      width: 140,
      render: (t: string) => <Tag>{reviewTypeLabel(t)}</Tag>,
    },
    {
      title: '风险等级',
      dataIndex: 'severity',
      key: 'severity',
      width: 80,
      render: (s: string) => <Tag color={severityColor(s)}>{s}</Tag>,
    },
    {
      title: '问题描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '依据来源',
      dataIndex: 'source_reference',
      key: 'source',
      width: 200,
    },
    {
      title: '修改建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: 300,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={4}>
        <AuditOutlined /> 临床试验文档智能审核
      </Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        选择审核类型后点击"开始审核"，系统将自动检索知识库中的方案、SOP、手册等文档，
        对上传的病例文件进行访视窗口、纳排标准、AE逻辑、文件一致性等方面的智能检查。
      </Text>

      {/* Review type selection */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={5}>审核类型</Title>
        <Select
          mode="multiple"
          value={selectedTypes}
          onChange={setSelectedTypes}
          style={{ width: '100%', marginBottom: 16 }}
          options={REVIEW_TYPES.map((r) => ({
            value: r.value,
            label: (
              <Space>
                {r.icon}
                {r.label}
              </Space>
            ),
          }))}
        />
        <Button
          type="primary"
          size="large"
          icon={<PlayCircleOutlined />}
          onClick={handleReview}
          loading={reviewing}
        >
          开始审核
        </Button>
      </Card>

      {/* Review results */}
      {reviewing && (
        <Card>
          <div style={{ textAlign: 'center', padding: 48 }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 16 }}>
              正在检索知识库文档并对病例进行智能审核...
            </Paragraph>
          </div>
        </Card>
      )}

      {hasReviewed && !reviewing && (
        <>
          {/* Summary */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Stat title="发现问题" value={findings.length} color="#1677ff" />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Stat
                  title="高风险"
                  value={findings.filter((f) => f.severity === '高').length}
                  color="#ff4d4f"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Stat
                  title="中风险"
                  value={findings.filter((f) => f.severity === '中').length}
                  color="#faad14"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Stat
                  title="低风险"
                  value={findings.filter((f) => f.severity === '低').length}
                  color="#1677ff"
                />
              </Card>
            </Col>
          </Row>

          {/* Findings table */}
          <Card
            title="审核结果详情"
            extra={
              <Button type="primary" ghost>
                导出审核报告
              </Button>
            }
          >
            <Table
              columns={columns}
              dataSource={findings.map((f, i) => ({ ...f, key: i }))}
              pagination={false}
              expandable={{
                expandedRowRender: (record) => (
                  <div style={{ padding: '8px 0' }}>
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="问题描述" span={2}>
                        {record.description}
                      </Descriptions.Item>
                      <Descriptions.Item label="依据来源">
                        {record.source_reference}
                      </Descriptions.Item>
                      <Descriptions.Item label="修改建议">
                        {record.suggestion}
                      </Descriptions.Item>
                    </Descriptions>
                  </div>
                ),
              }}
            />
          </Card>
        </>
      )}

      {!reviewing && !hasReviewed && (
        <Empty
          description="选择审核类型并点击开始审核"
          style={{ marginTop: 48 }}
        />
      )}
    </div>
  );
}

function Stat({ title, value, color }: { title: string; value: number; color: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ color: '#999', fontSize: 13 }}>{title}</div>
    </div>
  );
}
