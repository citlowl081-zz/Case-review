import { useEffect } from 'react';
import { useThemeStore } from '../store/themeStore';
import { theme as antdTheme, ConfigProvider } from 'antd';

export function useTheme() {
  const { mode, toggle, setTheme } = useThemeStore();

  useEffect(() => {
    // Apply theme to document body for CSS variables
    document.body.setAttribute('data-theme', mode);
  }, [mode]);

  return { mode, toggle, setTheme, isDark: mode === 'dark' };
}
