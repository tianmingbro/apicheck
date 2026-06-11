import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { authApi } from '@/services/modules/authApi';
import type { User, LoginDto } from '@/types/api.types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (credentials: LoginDto) => Promise<void>;
  logout: () => void;
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

          localStorage.setItem('access_token', access_token);

          set({
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Try to fetch user info (non-blocking)
          get().fetchCurrentUser().catch(() => {});
        } catch (error) {
          set({ isLoading: false, isAuthenticated: false, token: null, user: null });
          throw error;
        }
      },

      logout: () => {
        authApi.logout().catch(() => {});
        get().clearAuth();
      },

      fetchCurrentUser: async () => {
        try {
          const response = await authApi.getCurrentUser();
          set({ user: response.data });
        } catch {
          // /auth/me might not exist — that's OK, don't log out
          console.debug('Could not fetch current user (endpoint may not exist)');
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
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user }),
    },
  ),
);
