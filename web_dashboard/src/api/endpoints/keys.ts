import client from '../client';
import type { APIKey, CreateKeyPayload } from '@/api/types/api.types';

export const keysApi = {
  list: () => client.get<APIKey[]>('/keys/'),
  create: (data: CreateKeyPayload) => client.post<APIKey>('/keys/', data),
  delete: (id: number) => client.delete(`/keys/${id}`),
};
