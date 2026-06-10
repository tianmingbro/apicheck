// src/router/index.tsx
import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import PrivateRoute from '@/components/layout/PrivateRoute';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AdminLayout from '@/pages/admin/AdminLayout';
import GlobalLogsPage from '@/pages/admin/GlobalLogsPage';

// 用户端页面（懒加载）
const Login = lazy(() => import('@/pages/auth/Login'));
const Register = lazy(() => import('@/pages/auth/Register'));
const UsageDashboard = lazy(() => import('@/pages/dashboard/UsageDashboard'));
const KeysManagement = lazy(() => import('@/pages/keys/KeysManagement'));
const PlansPage = lazy(() => import('@/pages/billing/PlansPage'));

// 管理员页面（懒加载）
const UserManagement = lazy(() => import('@/pages/admin/UserManagement'));
const KeyManagement = lazy(() => import('@/pages/admin/KeyManagement'));
const LogAudit = lazy(() => import('@/pages/admin/LogAudit'));

// 统一懒加载包装器
const withSuspense = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<div className="flex h-screen items-center justify-center">加载中...</div>}>
    <Component />
  </Suspense>
);

export const router = createBrowserRouter([
  // 公开路由
  {
    path: '/login',
    element: withSuspense(Login),
  },
  {
    path: '/register',
    element: withSuspense(Register),
  },
  // 用户端私有路由
  {
    path: '/',
    element: (
      <PrivateRoute>
        <DashboardLayout />
      </PrivateRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: withSuspense(UsageDashboard) },   // 使用 UsageDashboard
      { path: 'keys', element: withSuspense(KeysManagement) },
      { path: 'billing', element: withSuspense(PlansPage) },         // 使用 PlansPage
    ],
  },
  // 管理员私有路由（同样使用 PrivateRoute 进行登录检查）
  {
    path: '/admin',
    element: (
      <PrivateRoute>
        <AdminLayout />
      </PrivateRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/admin/users" replace /> },
      { path: 'users', element: withSuspense(UserManagement) },
      { path: 'keys', element: withSuspense(KeyManagement) },
      { path: 'logs', element: withSuspense(LogAudit) },
      { path: 'logs', element: <GlobalLogsPage /> }
    ],
  },
]);