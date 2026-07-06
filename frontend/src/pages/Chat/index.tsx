import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Input,
  Button,
  List,
  Typography,
  Popconfirm,
  Empty,
  message,
  Spin,
  Tag,
  Card,
  Tooltip,
  Badge,
} from 'antd';
import {
  SendOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  StopOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useChat } from '../../hooks/useChat';
import { useAuth } from '../../hooks/useAuth';
import { useThemeStore } from '../../store/themeStore';
import type { ChatMessage, Citation } from '../../types';
import { formatDateTime } from '../../utils/format';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

export default function ChatPage() {
  const { user } = useAuth();
  const isDark = useThemeStore((s) => s.mode === 'dark');
  const {
    sessions,
    currentSessionId,
    messages,
    citations,
    isStreaming,
    streamingContent,
    loadSessions,
    createSession,
    deleteSession,
    renameSession,
    selectSession,
    sendMessage,
    stopStreaming,
    submitFeedback,
  } = useChat();

  const [inputValue, setInputValue] = useState('');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [activeCitation, setActiveCitation] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isStreaming) return;
    setInputValue('');
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSend();
    }
  };

  const handleNewSession = async () => {
    await createSession();
  };

  const handleRename = async (id: string) => {
    if (editTitle.trim()) {
      await renameSession(id, editTitle.trim());
    }
    setEditingSessionId(null);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  const sessionCount = sessions.length;

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* ── Session Sidebar ── */}
      <div
        style={{
          width: 280,
          minWidth: 280,
          borderRight: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
          display: 'flex',
          flexDirection: 'column',
          background: isDark ? '#141414' : '#fafafa',
        }}
      >
        <div style={{ padding: '12px 16px', borderBottom: `1px solid ${isDark ? '#303030' : '#f0f0f0'}` }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={handleNewSession}
          >
            新建对话
          </Button>
        </div>

        <div style={{ flex: 1, overflow: 'auto' }}>
          {sessions.length === 0 ? (
            <Empty
              description="暂无会话"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 48 }}
            />
          ) : (
            <List
              dataSource={sessions}
              renderItem={(s) => (
                <div
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  style={{
                    padding: '10px 16px',
                    cursor: 'pointer',
                    background:
                      currentSessionId === s.id
                        ? isDark
                          ? '#1f1f1f'
                          : '#e6f4ff'
                        : 'transparent',
                    borderLeft:
                      currentSessionId === s.id ? '3px solid #1677ff' : '3px solid transparent',
                    transition: 'all 0.2s',
                  }}
                >
                  {editingSessionId === s.id ? (
                    <Input
                      size="small"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => handleRename(s.id)}
                      onPressEnter={() => handleRename(s.id)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text
                        ellipsis
                        style={{
                          flex: 1,
                          fontSize: 13,
                          color: currentSessionId === s.id ? '#1677ff' : undefined,
                        }}
                      >
                        {s.title}
                      </Text>
                      <div
                        style={{ display: 'flex', gap: 4, marginLeft: 8 }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Tooltip title="重命名">
                          <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined style={{ fontSize: 12 }} />}
                            onClick={() => {
                              setEditingSessionId(s.id);
                              setEditTitle(s.title);
                            }}
                          />
                        </Tooltip>
                        <Popconfirm
                          title="确认删除此会话？"
                          onConfirm={() => deleteSession(s.id)}
                          okText="删除"
                          cancelText="取消"
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined style={{ fontSize: 12 }} />}
                          />
                        </Popconfirm>
                      </div>
                    </div>
                  )}
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {formatDateTime(s.updated_at)} · {s.message_count} 条消息
                  </Text>
                </div>
              )}
            />
          )}
        </div>

        <div
          style={{
            padding: '8px 16px',
            borderTop: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
            fontSize: 12,
            color: '#999',
          }}
        >
          共 {sessionCount} 个会话
        </div>
      </div>

      {/* ── Chat Area ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: 'calc(100% - 280px)' }}>
        {/* Messages */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '16px 24px',
            background: isDark ? '#000' : '#fff',
          }}
        >
          {!currentSessionId ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
              }}
            >
              <MessageOutlined style={{ fontSize: 48, color: '#ccc', marginBottom: 16 }} />
              <Text type="secondary">选择或创建一个会话开始问答</Text>
              <Text type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
                支持 Ctrl+Enter 快捷发送
              </Text>
            </div>
          ) : messages.length === 0 && !isStreaming ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
              }}
            >
              <FileTextOutlined style={{ fontSize: 48, color: '#ccc', marginBottom: 16 }} />
              <Text type="secondary">开始提问临床试验相关问题</Text>
              <div style={{ marginTop: 16, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 500 }}>
                {[
                  '筛选期需要完成哪些检查？',
                  '试验药物保存温度是多少？',
                  'AE开始时间早于首次用药怎么判断？',
                  'V1和V2之间的访视窗口是多少天？',
                ].map((q) => (
                  <Tag
                    key={q}
                    style={{ cursor: 'pointer', marginBottom: 4 }}
                    onClick={() => {
                      setInputValue(q);
                      inputRef.current?.focus();
                    }}
                  >
                    {q}
                  </Tag>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isDark={isDark}
                  activeCitation={activeCitation}
                  setActiveCitation={setActiveCitation}
                  onCopy={handleCopy}
                  onFeedback={submitFeedback}
                />
              ))}

              {/* Streaming message */}
              {isStreaming && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: 16,
                  }}
                >
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '10px 16px',
                      borderRadius: 8,
                      background: isDark ? '#1f1f1f' : '#f0f0f0',
                    }}
                  >
                    <StreamingContent text={streamingContent} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Citations panel */}
        {citations.length > 0 && (isStreaming || messages.length > 0) && (
          <div
            style={{
              borderTop: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
              padding: '8px 16px',
              background: isDark ? '#141414' : '#fafafa',
              maxHeight: activeCitation ? 200 : 60,
              overflow: 'auto',
              transition: 'max-height 0.3s',
            }}
          >
            <Text type="secondary" style={{ fontSize: 12, marginBottom: 4, display: 'block' }}>
              引用来源 ({citations.length})：
            </Text>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {citations.map((c, i) => (
                <Card
                  key={i}
                  size="small"
                  hoverable
                  onClick={() => setActiveCitation(activeCitation === i ? null : i)}
                  style={{
                    cursor: 'pointer',
                    borderColor: activeCitation === i ? '#1677ff' : undefined,
                    maxWidth: 300,
                  }}
                  title={
                    <Text style={{ fontSize: 12 }}>[{c.index}] {c.doc_name}</Text>
                  }
                >
                  {activeCitation === i && (
                    <Text style={{ fontSize: 12 }}>{c.chunk_text}</Text>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        {currentSessionId && (
          <div
            style={{
              borderTop: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
              padding: '12px 24px',
              background: isDark ? '#141414' : '#fff',
            }}
          >
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  isStreaming ? '正在生成回答...' : '输入问题，Ctrl+Enter 发送'
                }
                autoSize={{ minRows: 1, maxRows: 5 }}
                disabled={isStreaming}
                style={{ flex: 1 }}
              />
              {isStreaming ? (
                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={stopStreaming}
                >
                  停止
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  disabled={!inputValue.trim()}
                >
                  发送
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Message Bubble ──
function MessageBubble({
  message: msg,
  isDark,
  activeCitation,
  setActiveCitation,
  onCopy,
  onFeedback,
}: {
  message: ChatMessage;
  isDark: boolean;
  activeCitation: number | null;
  setActiveCitation: (n: number | null) => void;
  onCopy: (text: string) => void;
  onFeedback: (id: string, fb: number) => Promise<void>;
}) {
  const isUser = msg.role === 'user';

  // Parse [1], [2] citation markers in assistant messages
  const renderContent = (content: string) => {
    if (isUser) return content;

    // Replace citation markers [1], [2] etc with clickable tags
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const idx = parseInt(match[1]) - 1;
        return (
          <Tag
            key={i}
            color={activeCitation === idx ? 'blue' : 'default'}
            style={{ cursor: 'pointer', margin: '0 2px' }}
            onClick={() => setActiveCitation(activeCitation === idx ? null : idx)}
          >
            [{match[1]}]
          </Tag>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
      }}
    >
      <div style={{ maxWidth: '80%' }}>
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            background: isUser
              ? '#1677ff'
              : isDark
              ? '#1f1f1f'
              : '#f0f0f0',
            color: isUser ? '#fff' : isDark ? '#e8e8e8' : '#333',
          }}
        >
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.6 }}>
            {renderContent(msg.content)}
          </div>

          {/* Citations in message */}
          {!isUser && msg.citations && msg.citations.length > 0 && (
            <div style={{ marginTop: 12, borderTop: '1px solid rgba(0,0,0,0.1)', paddingTop: 8 }}>
              <Text type={isUser ? undefined : 'secondary'} style={{ fontSize: 11 }}>
                📎 引用来源：
              </Text>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
                {msg.citations.map((c, i) => (
                  <Tag
                    key={i}
                    style={{ cursor: 'pointer', fontSize: 11 }}
                    onClick={() => setActiveCitation(activeCitation === i ? null : i)}
                  >
                    [{c.index}] {c.doc_name}
                  </Tag>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            marginTop: 4,
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            paddingLeft: isUser ? 0 : 8,
            paddingRight: isUser ? 8 : 0,
          }}
        >
          <Text type="secondary" style={{ fontSize: 11 }}>
            {formatDateTime(msg.created_at)}
          </Text>
          {!isUser && (
            <>
              <Tooltip title="复制">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: 12 }} />}
                  onClick={() => onCopy(msg.content)}
                />
              </Tooltip>
              <Tooltip title="有用">
                <Button
                  type="text"
                  size="small"
                  icon={
                    <LikeOutlined
                      style={{
                        fontSize: 12,
                        color: msg.feedback === 1 ? '#1677ff' : undefined,
                      }}
                    />
                  }
                  onClick={() => onFeedback(msg.id, msg.feedback === 1 ? 0 : 1)}
                />
              </Tooltip>
              <Tooltip title="无用">
                <Button
                  type="text"
                  size="small"
                  icon={
                    <DislikeOutlined
                      style={{
                        fontSize: 12,
                        color: msg.feedback === -1 ? '#ff4d4f' : undefined,
                      }}
                    />
                  }
                  onClick={() => onFeedback(msg.id, msg.feedback === -1 ? 0 : -1)}
                />
              </Tooltip>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Streaming Content ──
function StreamingContent({ text }: { text: string }) {
  return (
    <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.6 }}>
      {text}
      {text && (
        <span
          style={{
            display: 'inline-block',
            width: 2,
            height: 16,
            backgroundColor: '#1677ff',
            marginLeft: 2,
            animation: 'blink 1s step-end infinite',
            verticalAlign: 'middle',
          }}
        />
      )}
    </div>
  );
}
