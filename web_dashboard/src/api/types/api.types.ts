export interface APIKey {
  id: number;
  key: string;
  base_url?: string;
  is_enabled: boolean;
  created_at: string;
  total_calls: number;
  last_used_at?: string;
}

export interface CreateKeyPayload {
  key_value: string;
  base_url?: string;
}

export interface User {
  id: number;
  username: string;
  role: string;
}

export interface UsageStats {
  total_calls: number;
  total_tokens: number;
  remaining_quota: number;
}
