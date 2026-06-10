// src/services/modules/authApi.ts
import apiClient from '../apiClient';
import type { LoginDto, AuthResponse, User } from '@/types/api.types';

export const authApi = {
  /**
   * 登录
   * @param data - 登录凭证（username/password）
   * @returns Promise<AuthResponse>
   */
  login: (data: LoginDto) =>
    apiClient.post<AuthResponse>('/auth/login', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      transformRequest: [(data) => new URLSearchParams(data).toString()],
    }),

  /**
   * 获取当前用户信息（示例接口，根据实际后端调整）
   * @returns Promise<User>
   */
  getCurrentUser: () => apiClient.get<User>('/auth/me'),

  /**
   * 登出（可选，通知后端失效 token）
   */
  logout: () => apiClient.post('/auth/logout'),
};