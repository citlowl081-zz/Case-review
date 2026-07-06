import { useCallback } from 'react';
import { useChatStore } from '../store/chatStore';

export function useChat() {
  const store = useChatStore();

  return {
    sessions: store.sessions,
    currentSessionId: store.currentSessionId,
    messages: store.messages,
    citations: store.citations,
    isStreaming: store.isStreaming,
    streamingContent: store.streamingContent,

    loadSessions: store.loadSessions,
    createSession: store.createSession,
    deleteSession: store.deleteSession,
    renameSession: store.renameSession,
    selectSession: store.selectSession,
    sendMessage: store.sendMessage,
    stopStreaming: store.stopStreaming,
    loadMessages: store.loadMessages,
    submitFeedback: store.submitFeedback,
    clearState: store.clearState,
  };
}
