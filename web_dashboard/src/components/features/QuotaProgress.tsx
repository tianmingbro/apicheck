// src/components/features/QuotaProgress.tsx
interface QuotaProgressProps {
  used: number;      // 已使用额度
  limit: number;     // 总额度
  unit?: string;     // 单位，默认 "次"
}

export default function QuotaProgress({ used, limit, unit = '次' }: QuotaProgressProps) {
  const percentage = limit > 0 ? (used / limit) * 100 : 0;
  const remaining = limit - used;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-neutral-600 dark:text-neutral-400">已使用</span>
        <span className="font-medium text-neutral-900 dark:text-white">
          {used.toLocaleString()} / {limit.toLocaleString()} {unit}
        </span>
      </div>
      <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-neutral-500 dark:text-neutral-400">
        <span>剩余: {remaining.toLocaleString()} {unit}</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>
    </div>
  );
}