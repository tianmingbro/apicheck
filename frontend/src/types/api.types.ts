// src/types/api.types.ts
export interface User {
  id: number;
  username: string;
  email?: string;
  role: 'user' | 'admin';
  createdAt: string;
}

export interface LoginDto {
  username: string;   // 邮箱作为用户名
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface CallLog {
  id: number;
  request_id: string;
  user_id: number;
  api_key_id: number | null;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_cents: number;
  status_code: number;
  duration_ms: number;
  error_message: string | null;
  created_at: string;
}