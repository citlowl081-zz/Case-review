import { create } from 'zustand';
import type { UserInfo } from '../types';
import { getToken, setToken, removeToken } from '../utils/token';
import * as authService from '../services/auth';

interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  changePassword: (oldPwd: string, newPwd: string, confirmPwd: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!getToken(),
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      const res = await authService.login({ username, password });
      setToken(res.access_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  register: async (username, password, confirmPassword) => {
    set({ isLoading: true });
    try {
      const res = await authService.register({
        username,
        password,
        confirm_password: confirmPassword,
      });
      setToken(res.access_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  logout: () => {
    removeToken();
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    if (!getToken()) return;
    set({ isLoading: true });
    try {
      const user = await authService.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      removeToken();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  changePassword: async (oldPwd, newPwd, confirmPwd) => {
    await authService.changePassword({
      old_password: oldPwd,
      new_password: newPwd,
      confirm_password: confirmPwd,
    });
  },
}));
