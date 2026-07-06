// ── User ──
export interface UserInfo {
  id: string;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  confirm_password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

// ── Session ──
export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// ── Chat ──
export interface Citation {
  index: number;
  doc_name: string;
  chunk_text: string;
  page?: number;
  chunk_id?: string;
  score?: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  feedback?: number | null;
  created_at: string;
}

export interface SSEEvent {
  type: 'token' | 'citations' | 'done' | 'error';
  content?: string;
  citations?: Citation[];
  message?: string;
  message_id?: string;
  full_response?: string;
}

// ── Knowledge Base ──
export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  doc_category: string;
  file_size: number;
  status: string;
  chunk_count: number;
  error_message?: string;
  created_at: string;
}

export interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  total_size_bytes: number;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
}

export const DOC_CATEGORIES: Record<string, string> = {
  study_protocol: '研究方案',
  drug_manual: '药物管理手册',
  case_record: '病例记录',
  lab_report: '检查报告',
  ae_form: 'AE表',
  conmed: '合并用药表',
  visit_plan: '访视计划表',
  sop: 'SOP/GCP',
  other: '其他',
};

export const DOC_STATUS_LABELS: Record<string, string> = {
  uploading: '上传中',
  parsing: '解析中',
  embedding: '向量化中',
  completed: '已完成',
  failed: '处理失败',
};

// ── Clinical Review ──
export interface ReviewRequest {
  document_ids: string[];
  review_types: string[];
}

export interface ReviewFinding {
  review_type: string;
  severity: '高' | '中' | '低';
  description: string;
  source_reference: string;
  suggestion: string;
}

export interface ReviewResponse {
  document_id: string;
  document_name: string;
  findings: ReviewFinding[];
  summary: string;
  reviewed_at: string;
}
