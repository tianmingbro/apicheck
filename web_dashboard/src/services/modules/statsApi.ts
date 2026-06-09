// src/services/modules/statsApi.ts
import apiClient from '../apiClient';

// 每日调用数据项
export interface DailyCall {
  date: string;          // YYYY-MM-DD
  count: number;
}

// Token 消耗数据项
export interface TokenConsumption {
  date: string;
  inputTokens: number;
  outputTokens: number;
  total: number;
}

// 用量汇总数据
export interface UsageStats {
  dailyCalls: DailyCall[];
  tokenConsumed: TokenConsumption[];
  totalCalls: number;
  totalTokens: number;
  remainingQuota: number;
  quotaLimit: number;
}

export const statsApi = {
  /**
   * 获取当前用户的用量统计
   * @param days 查询最近 N 天（默认 30）
   */
  getUsage: (days: number = 30) =>
    apiClient.get<UsageStats>(`/stats/usage`, { params: { days } }),
};