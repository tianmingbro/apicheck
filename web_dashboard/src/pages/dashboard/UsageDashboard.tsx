// src/pages/dashboard/UsageDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { statsApi, type UsageStats } from '@/services/modules/statsApi';
import TrendChart from '@/components/features/TrendChart';
import QuotaProgress from '@/components/features/QuotaProgress';

// 模拟数据（仅用于开发演示，实际会被 API 覆盖）
const mockData: UsageStats = {
  dailyCalls: [
    { date: '2025-03-01', count: 23 },
    { date: '2025-03-02', count: 45 },
    { date: '2025-03-03', count: 38 },
    { date: '2025-03-04', count: 72 },
    { date: '2025-03-05', count: 56 },
    { date: '2025-03-06', count: 89 },
    { date: '2025-03-07', count: 104 },
  ],
  tokenConsumed: [],
  totalCalls: 427,
  totalTokens: 12500,
  remainingQuota: 4573,
  quotaLimit: 5000,
};

export default function UsageDashboard() {
  // 使用 React Query 获取真实数据（生产环境替换为真实 API）
  const { data, isLoading, error } = useQuery({
    queryKey: ['usage-stats'],
    queryFn: () => statsApi.getUsage(30),
    // 开发阶段使用模拟数据
    placeholderData: { data: mockData },
  });

  const stats = data?.data;

  if (error) {
    return (
      <div className="p-4 text-danger">
        加载失败: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">用量仪表盘</h1>

      {/* 总览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <OverviewCard title="总调用次数" value={stats?.totalCalls ?? 0} />
        <OverviewCard title="消耗 Tokens" value={stats?.totalTokens ?? 0} />
        <OverviewCard
          title="剩余配额"
          value={stats?.remainingQuota ?? 0}
          suffix={`/ ${stats?.quotaLimit ?? 0} 次`}
        />
      </div>

      {/* 进度条 */}
      {stats && (
        <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <h2 className="text-lg font-semibold mb-4">配额使用情况</h2>
          <QuotaProgress
            used={(stats.quotaLimit - stats.remainingQuota)}
            limit={stats.quotaLimit}
          />
        </div>
      )}

      {/* 趋势图 */}
      <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <h2 className="text-lg font-semibold mb-4">每日调用趋势</h2>
        <TrendChart
          data={stats?.dailyCalls ?? []}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

// 卡片子组件
function OverviewCard({ title, value, suffix = '' }: { title: string; value: number; suffix?: string }) {
  return (
    <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
      <h3 className="text-sm font-medium text-neutral-500 dark:text-neutral-400">{title}</h3>
      <p className="text-3xl font-bold mt-2 text-neutral-900 dark:text-white">
        {value.toLocaleString()} {suffix}
      </p>
    </div>
  );
}