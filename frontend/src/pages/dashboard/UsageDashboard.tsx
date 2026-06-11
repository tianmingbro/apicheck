// src/pages/dashboard/UsageDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { statsApi } from '@/services/modules/statsApi';
import TrendChart from '@/components/features/TrendChart';
import QuotaProgress from '@/components/features/QuotaProgress';

// Convert backend daily breakdown to chart-compatible format
interface ChartPoint {
  date: string;
  count: number;
}

export default function UsageDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['usage-stats'],
    queryFn: () => statsApi.getUsage(30),
  });

  const stats = data?.data;

  if (error) {
    return (
      <div className="p-4 text-danger">
        加载失败: {(error as Error).message}
      </div>
    );
  }

  // Transform daily breakdown for chart (backend: {date, calls, tokens} → chart: {date, count})
  const chartData: ChartPoint[] = (stats?.daily || []).map((d) => ({
    date: d.date,
    count: d.calls,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">用量仪表盘</h1>

      {/* 总览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <OverviewCard title="总调用次数" value={stats?.total_calls ?? 0} />
        <OverviewCard title="消耗 Tokens" value={stats?.total_tokens ?? 0} />
        <OverviewCard
          title="剩余配额"
          value={stats?.remaining_quota ?? 0}
          suffix={`/ ${stats?.quota_limit ?? 0} 次`}
        />
      </div>

      {/* 进度条 */}
      {stats && (
        <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
          <h2 className="text-lg font-semibold mb-4">配额使用情况</h2>
          <QuotaProgress
            used={stats.quota_used}
            limit={stats.quota_limit}
          />
        </div>
      )}

      {/* 趋势图 */}
      <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-700">
        <h2 className="text-lg font-semibold mb-4">每日调用趋势</h2>
        <TrendChart
          data={chartData}
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
