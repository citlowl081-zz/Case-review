import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Avatar, Dropdown, theme as antdTheme } from 'antd';
import {
  MessageOutlined,
  DatabaseOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  AuditOutlined,
  UserOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';
import ThemeToggle from '../ThemeToggle';

const { Header, Sider, Content } = Layout;

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const mode = useThemeStore((s) => s.mode);
  const isDark = mode === 'dark';

  const isAdmin = user?.role === 'admin';

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '知识库问答',
    },
    ...(isAdmin
      ? [
          {
            key: '/knowledge',
            icon: <DatabaseOutlined />,
            label: '知识库管理',
          },
          {
            key: '/review',
            icon: <AuditOutlined />,
            label: '智能审核',
          },
        ]
      : []),
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '个人设置',
    },
  ];

  const userMenuItems = [
    {
      key: 'role',
      label: `${isAdmin ? '管理员' : '普通用户'}: ${user?.username}`,
      disabled: true,
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme={isDark ? 'dark' : 'light'}
        style={{
          borderRight: isDark ? '1px solid #303030' : '1px solid #f0f0f0',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 16px',
          }}
        >
          <ExperimentOutlined
            style={{ fontSize: collapsed ? 20 : 24, color: '#1677ff' }}
          />
          {!collapsed && (
            <span
              style={{
                marginLeft: 10,
                fontSize: 14,
                fontWeight: 600,
                whiteSpace: 'nowrap',
                color: isDark ? '#e8e8e8' : '#333',
              }}
            >
              临床试验RAG
            </span>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          theme={isDark ? 'dark' : 'light'}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: isDark ? '#141414' : '#fff',
            borderBottom: isDark ? '1px solid #303030' : '1px solid #f0f0f0',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <ThemeToggle />
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
            >
              <Avatar
                icon={<UserOutlined />}
                style={{ cursor: 'pointer', backgroundColor: '#1677ff' }}
              />
            </Dropdown>
          </div>
        </Header>
        <Content
          style={{
            margin: 0,
            padding: 0,
            background: isDark ? '#000' : '#f5f5f5',
            height: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
