import React, { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Upload,
  Modal,
  Select,
  Tag,
  Popconfirm,
  message,
  Space,
  Typography,
  Statistic,
  Row,
  Col,
  Card,
  Progress,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  InboxOutlined,
  ReloadOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileTextOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getDocuments, deleteDocument, uploadDocument, getKnowledgeStats } from '../../services/knowledge';
import type { DocumentInfo, KnowledgeStats } from '../../types';
import { DOC_CATEGORIES, DOC_STATUS_LABELS } from '../../types';
import { formatFileSize, formatDateTime } from '../../utils/format';

const { Dragger } = Upload;
const { Text, Title } = Typography;

function FileIcon({ type }: { type: string }) {
  const style = { fontSize: 20 };
  switch (type) {
    case 'pdf': return <FilePdfOutlined style={{ ...style, color: '#ff4d4f' }} />;
    case 'docx': case 'doc': return <FileWordOutlined style={{ ...style, color: '#1677ff' }} />;
    case 'xlsx': case 'csv': return <FileExcelOutlined style={{ ...style, color: '#52c41a' }} />;
    default: return <FileTextOutlined style={style} />;
  }
}

function StatusTag({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    uploading: 'processing',
    parsing: 'processing',
    embedding: 'processing',
    completed: 'success',
    failed: 'error',
  };
  return (
    <Tag color={colorMap[status] || 'default'}>
      {DOC_STATUS_LABELS[status] || status}
    </Tag>
  );
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadCategory, setUploadCategory] = useState('other');
  const [uploading, setUploading] = useState(false);
  const [page, setPage] = useState(1);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await getDocuments({ page, page_size: 20 });
      setDocuments(res.documents);
      setTotal(res.total);
    } catch {
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await getKnowledgeStats();
      setStats(res);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, [page]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const res = await uploadDocument(file, uploadCategory);
      message.success(`${res.filename} 上传成功，正在后台处理`);
      setUploadModalOpen(false);
      fetchDocuments();
      fetchStats();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
    return false; // Prevent default upload behavior
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      message.success('文档已删除');
      fetchDocuments();
      fetchStats();
    } catch {
      message.error('删除失败');
    }
  };

  const columns: ColumnsType<DocumentInfo> = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (name: string, record) => (
        <Space>
          <FileIcon type={record.file_type} />
          <Text ellipsis style={{ maxWidth: 300 }}>{name}</Text>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'doc_category',
      key: 'category',
      width: 120,
      render: (cat: string) => (
        <Tag>{DOC_CATEGORIES[cat] || cat}</Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => <StatusTag status={status} />,
    },
    {
      title: '分块',
      dataIndex: 'chunk_count',
      key: 'chunks',
      width: 80,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (t: string) => formatDateTime(t),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Popconfirm
          title="确认删除此文档？"
          description="删除后将同时移除向量数据"
          onConfirm={() => handleDelete(record.id)}
          okText="删除"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  const completedDocs = stats?.by_status?.['completed'] || 0;
  const totalDocs = stats?.total_documents || 0;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>知识库管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => { fetchDocuments(); fetchStats(); }}>
            刷新
          </Button>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>
            上传文档
          </Button>
        </Space>
      </div>

      {/* Stats Cards */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic title="文档总数" value={stats.total_documents} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="向量块数" value={stats.total_chunks} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="存储大小"
                value={formatFileSize(stats.total_size_bytes)}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="处理完成率"
                value={totalDocs > 0 ? Math.round((completedDocs / totalDocs) * 100) : 0}
                suffix="%"
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Category distribution */}
      {stats && Object.keys(stats.by_category).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {Object.entries(stats.by_category).map(([cat, count]) => (
            <Tag key={cat}>{DOC_CATEGORIES[cat] || cat}: {count}</Tag>
          ))}
        </div>
      )}

      <Table
        columns={columns}
        dataSource={documents}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 个文档`,
        }}
      />

      {/* Upload Modal */}
      <Modal
        title="上传文档"
        open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <Text strong>文档分类：</Text>
          <Select
            value={uploadCategory}
            onChange={setUploadCategory}
            style={{ width: 200, marginLeft: 8 }}
            options={Object.entries(DOC_CATEGORIES).map(([value, label]) => ({
              value,
              label,
            }))}
          />
        </div>

        <Upload.Dragger
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx"
          showUploadList={false}
          beforeUpload={(file) => {
            handleUpload(file);
            return false;
          }}
          disabled={uploading}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF、Word、TXT、Markdown、CSV、Excel 格式，单文件最大 50MB
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  );
}
