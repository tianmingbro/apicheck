import client from '../client';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (data: RegisterPayload) =>
    client.post<AuthResponse>('/auth/register', data),
  login: (data: LoginPayload) =>
    client.post<AuthResponse>('/auth/login', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      transformRequest: [(data) => new URLSearchParams(data).toString()],
    }),
};