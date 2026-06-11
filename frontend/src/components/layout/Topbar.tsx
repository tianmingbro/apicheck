// src/components/layout/Topbar.tsx
import { Menu, User } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const user = useAuthStore((state) => state.user);

  return (
    <header className="bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 px-4 py-3 flex items-center justify-between">
      {/* 左侧：菜单按钮 + 标题（移动端显示） */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-700"
          aria-label="打开菜单"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="text-lg font-semibold lg:hidden">KEYPILOT</span>
      </div>

      {/* 右侧：用户信息 */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            {user?.username || '用户'}
          </span>
        </div>
        {/* 登出按钮（桌面端可选，侧边栏已有，这里不重复） */}
      </div>
    </header>
  );
}