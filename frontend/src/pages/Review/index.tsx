import React, { useEffect, useState } from 'react';
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
  Row,
  Col,
} from 'antd';
import {
  AuditOutlined,
  PlayCircleOutlined,
  WarningOutlined,
  FileSearchOutlined,
  ClockCircleOutlined,
  FileSyncOutlined,
} from '@ant-design/icons';
import { getDocuments, reviewDocuments } from '../../services/knowledge';
import type { DocumentInfo } from '../../types';

const { Title, Text, Paragraph } = Typography;

const REVIEW_TYPES = [
  { value: 'visit_window', label: '访视时间窗审核', icon: <ClockCircleOutlined /> },
  { value: 'inclusion_exclusion', label: '纳排标准审核', icon: <FileSearchOutlined /> },
  { value: 'ae_logic', label: 'AE时间逻辑审核', icon: <WarningOutlined /> },
  { value: 'consistency', label: '文档一致性审核', icon: <FileSyncOutlined /> },
];

interface Finding {
  review_type: string;
  severity: string;
  description: string;
  source_reference: string;
  suggestion: string;
}

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
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    REVIEW_TYPES.map((r) => r.value)
  );
  const [reviewing, setReviewing] = useState(false);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [summary, setSummary] = useState('');
  const [hasReviewed, setHasReviewed] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setDocsLoading(true);
    try {
      const res = await getDocuments({ page: 1, page_size: 100, status: 'completed' });
      setDocuments(res.documents);
    } catch {
      message.error('获取文档列表失败');
    } finally {
      setDocsLoading(false);
    }
  };

  const handleReview = async () => {
    if (selectedTypes.length === 0) {
      message.warning('请选择至少一种审核类型');
      return;
    }
    if (selectedDocIds.length === 0) {
      message.warning('请选择至少一份待审核文档');
      return;
    }
    setReviewing(true);
    setHasReviewed(false);
    try {
      const result = await reviewDocuments({
        document_ids: selectedDocIds,
        review_types: selectedTypes,
      });
      setFindings(result.findings || []);
      setSummary(result.summary || '');
      setHasReviewed(true);
      message.success(`审核完成，发现 ${result.findings?.length || 0} 个问题`);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '审核失败，请重试');
    } finally {
      setReviewing(false);
    }
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
      render: (text: string) => (
        <Text ellipsis style={{ maxWidth: 180 }} title={text}>
          {text}
        </Text>
      ),
    },
    {
      title: '修改建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: 300,
      render: (text: string) => (
        <Text ellipsis style={{ maxWidth: 280 }} title={text}>
          {text}
        </Text>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={4}>
        <AuditOutlined /> 临床试验文档智能审核
      </Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        从知识库中选择已完成处理的文档，选择审核类型后点击"开始审核"，
        系统将自动对目标文档进行访视窗口、纳排标准、AE逻辑、文件一致性等方面的智能检查。
      </Text>

      {/* Document + Review Type Selection */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={5}>待审核文档</Title>
        <Select
          mode="multiple"
          value={selectedDocIds}
          onChange={setSelectedDocIds}
          style={{ width: '100%', marginBottom: 16 }}
          placeholder="选择已完成处理的文档（可多选）"
          loading={docsLoading}
          options={documents.map((d) => ({
            value: d.id,
            label: `${d.filename} (${d.file_type.toUpperCase()}, ${d.chunk_count || 0} 块)`,
          }))}
          notFoundContent={
            docsLoading ? <Spin size="small" /> : <Empty description="暂无已完成处理的文档，请先上传文档" />
          }
        />

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

      {/* Loading */}
      {reviewing && (
        <Card>
          <div style={{ textAlign: 'center', padding: 48 }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 16 }}>
              正在检索知识库文档并对选中文档进行智能审核...
            </Paragraph>
            <Text type="secondary">审核大型文档可能需要 30-60 秒，请耐心等待</Text>
          </div>
        </Card>
      )}

      {/* Results */}
      {hasReviewed && !reviewing && (
        <>
          {/* Summary */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <StatBlock title="发现问题" value={findings.length} color="#1677ff" />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <StatBlock
                  title="高风险"
                  value={findings.filter((f) => f.severity === '高').length}
                  color="#ff4d4f"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <StatBlock
                  title="中风险"
                  value={findings.filter((f) => f.severity === '中').length}
                  color="#faad14"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <StatBlock
                  title="低风险"
                  value={findings.filter((f) => f.severity === '低').length}
                  color="#1677ff"
                />
              </Card>
            </Col>
          </Row>

          {/* Summary text */}
          {summary && (
            <Card size="small" style={{ marginBottom: 16 }}>
              <Text strong>审核总结：</Text>
              <Text>{summary}</Text>
            </Card>
          )}

          {/* Findings table */}
          <Card
            title="审核结果详情"
            extra={
              findings.length > 0 && (
                <Button
                  type="primary"
                  ghost
                  onClick={() => {
                    const text = findings
                      .map(
                        (f, i) =>
                          `[${i + 1}] ${reviewTypeLabel(f.review_type)} | 风险: ${f.severity}\n` +
                          `问题: ${f.description}\n` +
                          `依据: ${f.source_reference}\n` +
                          `建议: ${f.suggestion}\n`
                      )
                      .join('\n');
                    navigator.clipboard.writeText(text);
                    message.success('审核结果已复制到剪贴板');
                  }}
                >
                  复制审核报告
                </Button>
              )
            }
          >
            {findings.length === 0 ? (
              <Empty description="未发现问题，文档审核通过" />
            ) : (
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
            )}
          </Card>
        </>
      )}

      {/* Empty state */}
      {!reviewing && !hasReviewed && (
        <Empty
          description="选择待审核文档和审核类型，点击「开始审核」"
          style={{ marginTop: 48 }}
        />
      )}
    </div>
  );
}

function StatBlock({ title, value, color }: { title: string; value: number; color: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ color: '#999', fontSize: 13 }}>{title}</div>
    </div>
  );
}
