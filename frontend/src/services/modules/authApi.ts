import apiClient from '../apiClient';
import type { LoginDto, AuthResponse, User } from '@/types/api.types';

export const authApi = {
  /** Login with username + password (backend expects form-urlencoded) */
  login: (data: LoginDto) => {
    const params = new URLSearchParams();
    params.append('username', data.username);
    params.append('password', data.password);
    return apiClient.post<AuthResponse>('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  /** Register a new user */
  register: (data: { username: string; password: string }) =>
    apiClient.post<AuthResponse>('/api/auth/register', data),

  /** Get current user info */
  getCurrentUser: () => apiClient.get<User>('/api/auth/me'),

  /** Logout (notify backend, best-effort) */
  logout: () => apiClient.post('/api/auth/logout'),
};
