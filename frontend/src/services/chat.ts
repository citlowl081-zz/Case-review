import { getToken } from '../utils/token';
import type { ChatMessage, SSEEvent } from '../types';

export async function getMessages(sessionId: string): Promise<{ messages: ChatMessage[]; total: number }> {
  const res = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) throw new Error('获取消息失败');
  return res.json();
}

export function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onCitations: (citations: any[]) => void,
  onDone: (fullResponse: string) => void,
  onError: (error: string) => void
): AbortController {
  const controller = new AbortController();
  const token = getToken();

  fetch(`/api/chat/sessions/${sessionId}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json();
        onError(err.detail || '请求失败');
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError('无法读取响应流');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: SSEEvent = JSON.parse(line.slice(6));
              switch (event.type) {
                case 'token':
                  if (event.content) {
                    fullResponse += event.content;
                    onToken(event.content);
                  }
                  break;
                case 'citations':
                  if (event.citations) {
                    onCitations(event.citations);
                  }
                  break;
                case 'done':
                  onDone(fullResponse || event.full_response || '');
                  break;
                case 'error':
                  onError(event.message || '未知错误');
                  break;
              }
            } catch {
              // Skip malformed SSE lines
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message || '网络错误');
      }
    });

  return controller;
}

export async function submitFeedback(
  sessionId: string,
  messageId: string,
  feedback: number
): Promise<void> {
  const res = await fetch(
    `/api/chat/sessions/${sessionId}/feedback/${messageId}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ feedback }),
    }
  );
  if (!res.ok) throw new Error('提交反馈失败');
}
