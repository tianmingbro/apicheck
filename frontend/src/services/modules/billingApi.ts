// src/services/modules/billingApi.ts
import apiClient from '../apiClient';

export interface Plan {
  id: number;
  name: string;           // 套餐名称（如 "Free Plan"）
  code: string;           // 唯一标识（free, pro, enterprise）
  price_cents: number;    // 价格（单位：分）
  currency: string;       // 货币（CNY）
  quota: number;          // 配额数量
  quota_unit: string;     // 配额单位（request / token）
  is_active: boolean;
  features: string[];     // 特性列表（由后端或前端映射）
}

export const billingApi = {
  /**
   * 获取所有套餐列表
   */
  getPlans: () => apiClient.get<Plan[]>('/api/plans'),

  /**
   * 获取当前用户订阅的套餐（可选）
   */
  getCurrentPlan: () => apiClient.get<Plan>('/api/plans/current'),
};