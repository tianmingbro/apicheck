// src/components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Key,
  CreditCard,
  Shield,
  LogOut,
  X,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);

  const isAdmin = user?.role === 'admin';

  const navItems = [
    { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
    { path: '/keys', label: 'API Keys', icon: Key },
    { path: '/billing', label: '账单与套餐', icon: CreditCard },
    ...(isAdmin ? [{ path: '/admin', label: '管理后台', icon: Shield }] : []),
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <>
      {/* 移动端遮罩层 */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
          aria-label="关闭侧边栏"
        />
      )}

      {/* 侧边栏容器 */}
      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-30
          w-64 bg-white dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700
          transform transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
      >
        {/* 头部 Logo 和关闭按钮 */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
          <h1 className="text-xl font-bold text-primary">KEYPILOT</h1>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-700"
            aria-label="关闭侧边栏"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 导航菜单 */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => {
                if (window.innerWidth < 1024) onClose(); // 移动端点击后关闭
              }}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2 rounded-md transition-colors ${
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* 底部登出按钮 */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-neutral-200 dark:border-neutral-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-2 text-danger hover:bg-danger/10 rounded-md transition-colors"
            aria-label="登出"
          >
            <LogOut className="w-5 h-5" />
            <span>登出</span>
          </button>
        </div>
      </aside>
    </>
  );
}