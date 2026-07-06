import { create } from 'zustand';
import type { ChatMessage, Citation, SessionInfo } from '../types';
import * as sessionService from '../services/session';
import * as chatService from '../services/chat';

interface ChatState {
  sessions: SessionInfo[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  citations: Citation[];
  isStreaming: boolean;
  streamingContent: string;
  abortController: AbortController | null;

  // Session actions
  loadSessions: () => Promise<void>;
  createSession: () => Promise<string>;
  deleteSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string) => Promise<void>;
  selectSession: (id: string) => Promise<void>;

  // Chat actions
  sendMessage: (content: string) => Promise<void>;
  stopStreaming: () => void;
  loadMessages: (sessionId: string) => Promise<void>;
  submitFeedback: (messageId: string, feedback: number) => Promise<void>;

  // State helpers
  clearState: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  citations: [],
  isStreaming: false,
  streamingContent: '',
  abortController: null,

  loadSessions: async () => {
    try {
      const res = await sessionService.getSessions();
      set({ sessions: res.sessions });
    } catch {
      // Silently fail
    }
  },

  createSession: async () => {
    const session = await sessionService.createSession();
    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSessionId: session.id,
      messages: [],
      citations: [],
    }));
    return session.id;
  },

  deleteSession: async (id) => {
    await sessionService.deleteSession(id);
    set((state) => {
      const sessions = state.sessions.filter((s) => s.id !== id);
      const newCurrentId = state.currentSessionId === id
        ? (sessions[0]?.id || null)
        : state.currentSessionId;
      return {
        sessions,
        currentSessionId: newCurrentId,
        messages: state.currentSessionId === id ? [] : state.messages,
      };
    });
  },

  renameSession: async (id, title) => {
    await sessionService.updateSession(id, title);
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, title } : s
      ),
    }));
  },

  selectSession: async (id) => {
    set({ currentSessionId: id });
    await get().loadMessages(id);
  },

  sendMessage: async (content) => {
    let sessionId = get().currentSessionId;
    if (!sessionId) {
      sessionId = await get().createSession();
    }

    // Add user message optimistically
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content,
      citations: [],
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isStreaming: true,
      streamingContent: '',
    }));

    const controller = chatService.streamChat(
      sessionId,
      content,
      // onToken
      (token) => {
        set((state) => ({
          streamingContent: state.streamingContent + token,
        }));
      },
      // onCitations
      (citations) => {
        set({ citations });
      },
      // onDone
      (fullResponse) => {
        // Reload messages from server to get proper IDs
        get().loadMessages(sessionId);
        get().loadSessions(); // Refresh session list for updated titles
        set({ isStreaming: false, streamingContent: '' });
      },
      // onError
      (error) => {
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          session_id: sessionId,
          role: 'assistant',
          content: `❌ ${error}`,
          citations: [],
          created_at: new Date().toISOString(),
        };
        set((state) => ({
          messages: [...state.messages, errorMsg],
          isStreaming: false,
          streamingContent: '',
        }));
      }
    );

    set({ abortController: controller });
  },

  stopStreaming: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
      set({ isStreaming: false, streamingContent: '', abortController: null });
    }
  },

  loadMessages: async (sessionId) => {
    try {
      const res = await chatService.getMessages(sessionId);
      set({ messages: res.messages });
    } catch {
      set({ messages: [] });
    }
  },

  submitFeedback: async (messageId, feedback) => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;
    await chatService.submitFeedback(currentSessionId, messageId, feedback);
    // Update local state
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, feedback } : m
      ),
    }));
  },

  clearState: () => {
    set({
      sessions: [],
      currentSessionId: null,
      messages: [],
      citations: [],
      isStreaming: false,
      streamingContent: '',
      abortController: null,
    });
  },
}));
