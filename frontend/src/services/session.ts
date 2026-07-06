import api from './api';
import type { SessionInfo } from '../types';

export async function getSessions(): Promise<{ sessions: SessionInfo[]; total: number }> {
  const res = await api.get('/sessions');
  return res.data;
}

export async function createSession(title?: string): Promise<SessionInfo> {
  const res = await api.post('/sessions', { title: title || '新对话' });
  return res.data;
}

export async function updateSession(id: string, title: string): Promise<SessionInfo> {
  const res = await api.patch(`/sessions/${id}`, { title });
  return res.data;
}

export async function deleteSession(id: string): Promise<void> {
  await api.delete(`/sessions/${id}`);
}
