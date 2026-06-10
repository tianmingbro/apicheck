// src/stores/authStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { authApi } from '@/services/modules/authApi';
import type { User, LoginDto } from '@/types/api.types';

interface AuthState {
  // 状态
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (credentials: LoginDto) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials: LoginDto) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(credentials);
          const { access_token } = response.data;

          // 存储 token 到 localStorage
          localStorage.setItem('access_token', access_token);
          
          // 更新 store 状态
          set({
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // 可选：登录成功后自动获取用户信息
          await get().fetchCurrentUser();
        } catch (error) {
          set({ isLoading: false, isAuthenticated: false, token: null });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          // 可选：通知后端失效 token（忽略失败）
          await authApi.logout().catch(() => {});
        } finally {
          // 清除本地存储
          localStorage.removeItem('access_token');
          // 重置 store 状态
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      fetchCurrentUser: async () => {
        try {
          const response = await authApi.getCurrentUser();
          set({ user: response.data });
        } catch (error) {
          console.error('Failed to fetch user info:', error);
          // 如果获取用户信息失败（如 token 无效），自动登出
          await get().logout();
        }
      },

      clearAuth: () => {
        localStorage.removeItem('access_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },
    }),
    {
      name: 'auth-storage',          // localStorage 键名
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user }), // 仅持久化 token 和 user
    }
  )
);