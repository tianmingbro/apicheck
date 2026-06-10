// src/pages/admin/AdminLayout.tsx
import { Outlet, Link } from 'react-router-dom';
import { Users, Key, FileText, LogOut } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

export default function AdminLayout() {
  const logout = useAuthStore(state => state.logout);
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-800 text-white">
        <div className="p-4 text-xl font-bold">Admin Panel</div>
        <nav className="mt-8">
          <Link to="/admin/users" className="flex items-center gap-3 px-4 py-2 hover:bg-gray-700">
            <Users size={18} /> 用户管理
          </Link>
          <Link to="/admin/keys" className="flex items-center gap-3 px-4 py-2 hover:bg-gray-700">
            <Key size={18} /> API Keys
          </Link>
          <Link to="/admin/logs" className="flex items-center gap-3 px-4 py-2 hover:bg-gray-700">
            <FileText size={18} /> 日志审计
          </Link>
        </nav>
        <button onClick={logout} className="absolute bottom-4 left-4 flex items-center gap-2">
          <LogOut size={18} /> 登出
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}