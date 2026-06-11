import apiClient from '../apiClient';
import type { UsageStats } from '@/types/api.types';

export const statsApi = {
  getUsage: (days: number = 30) =>
    apiClient.get<UsageStats>('/api/stats/usage', { params: { days } }),
};
