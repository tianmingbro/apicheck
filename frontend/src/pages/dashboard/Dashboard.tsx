import { useQuery } from '@tanstack/react-query';
import { statsApi } from '@/services/modules/statsApi';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { TrendingUp, Zap, Gauge, Activity } from 'lucide-react';

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stats', 'usage', 7],
    queryFn: () => statsApi.getUsage(7).then(r => r.data),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <div className="text-center py-12 text-neutral-500">加载中...</div>;
  }
  if (error || !data) {
    return <div className="text-center py-12 text-danger">加载失败，请稍后重试</div>;
  }

  const quotaPercent = data.quota_limit > 0
    ? Math.min(100, Math.round((data.quota_used / data.quota_limit) * 100))
    : 0;

  const chartData = data.daily.map(d => ({
    ...d,
    label: format(parseISO(d.date), 'MM/dd'),
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">仪表盘</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="总调用次数"
          value={data.total_calls.toLocaleString()}
          color="text-primary-500"
          bg="bg-primary-500/10"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="总 Token 消耗"
          value={data.total_tokens.toLocaleString()}
          color="text-warning"
          bg="bg-warning/10"
        />
        <StatCard
          icon={<Gauge className="w-5 h-5" />}
          label="剩余配额"
          value={data.remaining_quota.toLocaleString()}
          color="text-success"
          bg="bg-success/10"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="配额使用率"
          value={`${quotaPercent}%`}
          color="text-secondary-500"
          bg="bg-secondary-500/10"
        />
      </div>

      {/* Quota progress bar */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">配额使用进度</span>
          <span className="text-sm text-neutral-500">
            {data.quota_used.toLocaleString()} / {data.quota_limit.toLocaleString()}
            {data.extra_tokens > 0 && ` (+${data.extra_tokens.toLocaleString()} 额外)`}
          </span>
        </div>
        <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-3">
          <div
            className="h-3 rounded-full bg-primary-500 transition-all duration-500"
            style={{ width: `${quotaPercent}%` }}
          />
        </div>
      </div>

      {/* 7-day trend chart */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">近 7 天调用趋势</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
              formatter={(value: any, name: any) => [
                typeof value === 'number' ? value.toLocaleString() : String(value),
                name === 'tokens' ? 'Tokens' : '调用次数',
              ]}
            />
            <Bar dataKey="calls" fill="#3b82f6" radius={[4, 4, 0, 0]} name="calls" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({
  icon, label, value, color, bg,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-4 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${bg} ${color}`}>{icon}</div>
      <div>
        <p className="text-sm text-neutral-500 dark:text-neutral-400">{label}</p>
        <p className="text-xl font-bold text-neutral-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}
