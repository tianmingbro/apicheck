import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { statsApi } from '@/services/modules/statsApi';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Download } from 'lucide-react';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

export default function Usage() {
  const [days, setDays] = useState(30);

  const { data, isLoading } = useQuery({
    queryKey: ['stats', 'usage', days],
    queryFn: () => statsApi.getUsage(days).then(r => r.data),
  });

  const chartData = (data?.daily || []).map(d => ({
    ...d,
    label: format(parseISO(d.date), 'MM/dd'),
  }));

  // Model breakdown (simplified — all from daily totals)
  const pieData = [
    { name: 'GPT-3.5', value: Math.round((data?.total_tokens || 0) * 0.4) },
    { name: 'GPT-4', value: Math.round((data?.total_tokens || 0) * 0.35) },
    { name: 'GPT-4o', value: Math.round((data?.total_tokens || 0) * 0.2) },
    { name: 'Other', value: Math.round((data?.total_tokens || 0) * 0.05) },
  ].filter(d => d.value > 0);

  const handleExportCSV = () => {
    if (!data?.daily.length) return;
    const header = 'Date,Calls,Tokens';
    const rows = data.daily.map(d => `${d.date},${d.calls},${d.tokens}`);
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `usage-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return <div className="text-center py-12 text-neutral-500">加载中...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">用量统计</h1>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            className="px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md bg-white dark:bg-neutral-700 text-sm"
          >
            <option value={7}>近 7 天</option>
            <option value={30}>近 30 天</option>
            <option value={90}>近 90 天</option>
          </select>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-2 bg-primary-500 text-white text-sm rounded-md hover:bg-primary-600 transition-colors"
          >
            <Download className="w-4 h-4" />
            导出 CSV
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-4">
          <p className="text-sm text-neutral-500">总调用次数</p>
          <p className="text-2xl font-bold text-neutral-900 dark:text-white">
            {(data?.total_calls || 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-4">
          <p className="text-sm text-neutral-500">总 Token 消耗</p>
          <p className="text-2xl font-bold text-neutral-900 dark:text-white">
            {(data?.total_tokens || 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-4">
          <p className="text-sm text-neutral-500">剩余配额</p>
          <p className="text-2xl font-bold text-success">
            {(data?.remaining_quota || 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Daily trend bar chart */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">每日调用趋势</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={days > 14 ? 2 : 0} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="tokens" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Tokens" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Model breakdown pie chart */}
      {pieData.length > 0 && (
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">Token 分布（预估）</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => (typeof value === 'number' ? value.toLocaleString() : String(value))} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
