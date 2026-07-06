import React from 'react';
import { Navigate } from 'react-router-dom';
import { Result, Button } from 'antd';
import { useAuthStore } from '../../store/authStore';

interface Props {
  children: React.ReactNode;
}

export default function AdminGuard({ children }: Props) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'admin') {
    return (
      <Result
        status="403"
        title="权限不足"
        subTitle="此页面仅限管理员访问"
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回
          </Button>
        }
      />
    );
  }

  return <>{children}</>;
}
