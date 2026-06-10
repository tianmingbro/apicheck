import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export default function PrivateRoute() {
  const token = useAuthStore((state) => state.token);
  // 或者直接从 localStorage 读取，但用 store 更一致
  const isAuthenticated = !!token;

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}