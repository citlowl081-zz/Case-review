import React, { Suspense, lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';

const MainLayout = lazy(() => import('./components/Layout/MainLayout'));
const AdminGuard = lazy(() => import('./components/Layout/AdminGuard'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Chat = lazy(() => import('./pages/Chat'));
const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'));
const Review = lazy(() => import('./pages/Review'));
const Settings = lazy(() => import('./pages/Settings'));

function Loading() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Spin size="large" tip="加载中..." />
    </div>
  );
}

function Sus({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Loading />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Sus><Login /></Sus>,
  },
  {
    path: '/register',
    element: <Sus><Register /></Sus>,
  },
  {
    path: '/',
    element: <Sus><MainLayout /></Sus>,
    children: [
      {
        index: true,
        element: <Navigate to="/chat" replace />,
      },
      {
        path: 'chat',
        element: <Sus><Chat /></Sus>,
      },
      {
        path: 'knowledge',
        element: (
          <Sus>
            <AdminGuard>
              <KnowledgeBase />
            </AdminGuard>
          </Sus>
        ),
      },
      {
        path: 'review',
        element: (
          <Sus>
            <AdminGuard>
              <Review />
            </AdminGuard>
          </Sus>
        ),
      },
      {
        path: 'settings',
        element: <Sus><Settings /></Sus>,
      },
    ],
  },
]);
