import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/auth/Login';          // 使用我们之前实现的 Login 容器组件
import Dashboard from './pages/dashboard/Dashboard';
import KeysManagement from './pages/keys/KeysManagement';
import Usage from './pages/Usage';
import PrivateRoute from './components/common/PrivateRoute'; // 新增

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<Login />} />
          
          {/* 私有路由（需要登录） */}
          <Route element={<PrivateRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/keys" element={<KeysManagement />} />
              <Route path="/usage" element={<Usage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;