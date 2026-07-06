import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider, theme as antdTheme, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { router } from './router';
import { useAuthStore } from './store/authStore';
import { useThemeStore } from './store/themeStore';

export default function App() {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const mode = useThemeStore((s) => s.mode);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: mode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <RouterProvider router={router} />
      </AntApp>
    </ConfigProvider>
  );
}
