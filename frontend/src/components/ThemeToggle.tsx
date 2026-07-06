import React from 'react';
import { Button } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useThemeStore } from '../store/themeStore';

export default function ThemeToggle() {
  const { mode, toggle } = useThemeStore();

  return (
    <Button
      type="text"
      icon={mode === 'light' ? <MoonOutlined /> : <SunOutlined />}
      onClick={toggle}
      title={mode === 'light' ? '切换到深色模式' : '切换到浅色模式'}
    />
  );
}
