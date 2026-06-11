import apiClient from '../apiClient';

// ── Types ──────────────────────────────────────────────────
export interface AdminUser {
  id: number;
  username: string;
  role: string;
  quota_limit: number;
  quota_used: number;
  extra_tokens: number;
  created_at: string;
}

export interface AdminUserUpdate {
  role?: string;
  quota_limit?: number;
  extra_tokens?: number;
}

export interface AdminAPIKey {
  id: number;
  user_id: number;
  key_value: string;
  is_enabled: boolean;
  total_calls: number;
  last_used_at?: string;
}

export interface AdminCallLog {
  id: number;
  request_id: string;
  user_id: number;
  api_key_id: number | null;
  model: string;
  total_tokens: number;
  status_code: number;
  duration_ms: number;
  error_message: string | null;
  created_at: string;
}

export interface AdminLogsResponse {
  total: number;
  items: AdminCallLog[];
}

// ── API ────────────────────────────────────────────────────
export const adminApi = {
  // Users
  listUsers: (skip = 0, limit = 100) =>
    apiClient.get<AdminUser[]>('/api/admin/users', { params: { skip, limit } }),

  getUser: (userId: number) =>
    apiClient.get<AdminUser>(`/api/admin/users/${userId}`),

  updateUser: (userId: number, data: AdminUserUpdate) =>
    apiClient.patch(`/api/admin/users/${userId}`, data),

  deleteUser: (userId: number) =>
    apiClient.delete(`/api/admin/users/${userId}`),

  // API Keys
  listAllKeys: (skip = 0, limit = 100, userId?: number) =>
    apiClient.get<AdminAPIKey[]>('/api/admin/api-keys', {
      params: { skip, limit, user_id: userId },
    }),

  toggleKey: (keyId: number) =>
    apiClient.post<{ is_enabled: boolean }>(`/api/admin/api-keys/${keyId}/toggle`),

  // Logs
  listLogs: (params: Record<string, string | number | boolean>) =>
    apiClient.get<AdminLogsResponse>('/api/admin/logs', { params }),
};
