import client from '@/services/apiClient';
import type { APIKey, CreateKeyPayload } from '@/api/types/api.types';

export const keysApi = {
  list: () => client.get<APIKey[]>('/api/keys/'),
  create: (data: CreateKeyPayload) => client.post<APIKey>('/api/keys', data),
  delete: (id: number) => client.delete(`/api/keys/${id}`),
};
