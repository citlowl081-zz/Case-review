import api from './api';
import type { DocumentInfo, KnowledgeStats } from '../types';

export async function uploadDocument(
  file: File,
  category: string
): Promise<{ id: string; filename: string; status: string; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  const res = await api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function getDocuments(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  status?: string;
}): Promise<{ documents: DocumentInfo[]; total: number }> {
  const res = await api.get('/knowledge/documents', { params });
  return res.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/knowledge/documents/${id}`);
}

export async function getKnowledgeStats(): Promise<KnowledgeStats> {
  const res = await api.get('/knowledge/stats');
  return res.data;
}

export async function reviewDocuments(params: {
  document_ids: string[];
  review_types: string[];
}): Promise<{
  document_id: string;
  document_name: string;
  findings: Array<{
    review_type: string;
    severity: string;
    description: string;
    source_reference: string;
    suggestion: string;
  }>;
  summary: string;
  reviewed_at: string;
}> {
  const res = await api.post('/knowledge/review', params);
  return res.data;
}
