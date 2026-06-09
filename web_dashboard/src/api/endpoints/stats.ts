import client from '../client';
import type { UsageStats } from '@/api/types/api.types';

export const statsApi = {
  getUsage: () => client.get<UsageStats>('/stats/usage'),
};
