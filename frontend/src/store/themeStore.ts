import { create } from 'zustand';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  mode: ThemeMode;
  toggle: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const getInitialTheme = (): ThemeMode => {
  const saved = localStorage.getItem('theme_mode');
  if (saved === 'light' || saved === 'dark') return saved;
  return 'light';
};

export const useThemeStore = create<ThemeState>((set) => ({
  mode: getInitialTheme(),

  toggle: () => {
    set((state) => {
      const next = state.mode === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme_mode', next);
      return { mode: next };
    });
  },

  setTheme: (mode) => {
    localStorage.setItem('theme_mode', mode);
    set({ mode });
  },
}));
