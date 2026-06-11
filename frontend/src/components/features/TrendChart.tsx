// src/components/features/TrendChart.tsx
import { useMemo } from 'react';

interface TrendDataPoint {
  date: string;
  count: number;
}

interface TrendChartProps {
  data: TrendDataPoint[];
  isLoading?: boolean;
}

export default function TrendChart({ data, isLoading = false }: TrendChartProps) {
  const maxValue = useMemo(() => {
    if (!data.length) return 1;
    return Math.max(...data.map((d) => d.count), 1);
  }, [data]);

  if (isLoading) {
    return (
      <div className="h-48 bg-neutral-100 dark:bg-neutral-800 rounded animate-pulse" />
    );
  }

  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-neutral-500 dark:text-neutral-400 text-sm">
        暂无调用数据
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Bar chart */}
      <div className="flex items-end gap-1 h-36">
        {data.map((point, idx) => {
          const heightPct = (point.count / maxValue) * 100;
          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center justify-end"
              style={{ height: '100%' }}
            >
              <div
                className="w-full bg-primary/70 hover:bg-primary rounded-t transition-colors min-h-[2px]"
                style={{ height: `${Math.max(heightPct, 2)}%` }}
                title={`${point.date}: ${point.count} 次`}
              />
            </div>
          );
        })}
      </div>

      {/* X-axis labels */}
      <div className="flex gap-1">
        {data.map((point, idx) => (
          <div
            key={idx}
            className="flex-1 text-xs text-neutral-500 dark:text-neutral-400 text-center truncate"
            title={point.date}
          >
            {point.date.slice(5)} {/* Show MM-DD */}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex justify-end text-xs text-neutral-500 dark:text-neutral-400">
        最大: {maxValue.toLocaleString()} 次
      </div>
    </div>
  );
}
