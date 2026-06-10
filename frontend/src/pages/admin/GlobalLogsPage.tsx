import { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  SortingState,
  CellContext,
} from '@tanstack/react-table';
import { format } from 'date-fns';
import { Download, Search } from 'lucide-react';
import apiClient from '@/services/apiClient';
import type { CallLog } from '@/types/api.types';

// ========== 类型定义 ==========
interface LogsQueryParams {
  skip: number;
  limit: number;
  user_id?: string;
  model?: string;
  status_code?: string;
  start_time?: string;
  end_time?: string;
  order_by: string;
  order_desc: boolean;
}

interface LogsResponse {
  total: number;
  items: CallLog[];
}

// ========== API 调用函数 ==========
const fetchLogs = async (params: LogsQueryParams): Promise<LogsResponse> => {
  const response = await apiClient.get<LogsResponse>('/admin/logs', { params });
  return response.data;
};

export default function GlobalLogsPage() {
  // 筛选条件状态（明确类型）
  const [filters, setFilters] = useState<LogsQueryParams>({
    user_id: '',
    model: '',
    status_code: '',
    start_time: '',
    end_time: '',
    order_by: 'created_at',
    order_desc: true,
    skip: 0,
    limit: 100,
  });

  const [sorting, setSorting] = useState<SortingState>([{ id: 'created_at', desc: true }]);

  const { data, isLoading, refetch } = useQuery<LogsResponse>({
    queryKey: ['admin-logs', filters],
    queryFn: () => fetchLogs(filters),
    placeholderData: (previousData) => previousData,
  });

  useEffect(() => {
    if (sorting.length) {
      const sort = sorting[0];
      setFilters((prev) => ({
        ...prev,
        order_by: sort.id,
        order_desc: sort.desc,
        skip: 0,
      }));
    }
  }, [sorting]);

  // 导出 CSV
  const exportCSV = () => {
    if (!data?.items.length) return;
    const headers = ['ID', '用户ID', '请求ID', '模型', 'Token数', '状态码', '耗时(ms)', '错误信息', '时间'];
    const rows = data.items.map((log) => [
      log.id,
      log.user_id,
      log.request_id,
      log.model,
      log.total_tokens,
      log.status_code,
      log.duration_ms,
      log.error_message || '',
      format(new Date(log.created_at), 'yyyy-MM-dd HH:mm:ss'),
    ]);
    const csvContent = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `logs_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // 筛选条件变化处理（移除 any）
  const handleFilterChange = (key: keyof LogsQueryParams, value: string | number) => {
    setFilters((prev) => ({ ...prev, skip: 0, [key]: value }));
  };

  const handlePageChange = (newSkip: number) => {
    setFilters((prev) => ({ ...prev, skip: newSkip }));
  };

  // 表格列定义（修复 cell 类型）
  const columns = useMemo(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      { accessorKey: 'user_id', header: '用户ID', size: 80 },
      { accessorKey: 'request_id', header: '请求ID', size: 200 },
      { accessorKey: 'model', header: '模型' },
      { accessorKey: 'total_tokens', header: 'Token数' },
      { accessorKey: 'status_code', header: '状态码' },
      { accessorKey: 'duration_ms', header: '耗时(ms)' },
      { accessorKey: 'error_message', header: '错误信息' },
      {
        accessorKey: 'created_at',
        header: '时间',
        cell: ({ getValue }: CellContext<CallLog, unknown>) =>
          format(new Date(getValue() as string), 'yyyy-MM-dd HH:mm:ss'),
      },
    ],
    []
  );

  const table = useReactTable({
    data: data?.items || [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
  });

  const totalPages = Math.ceil((data?.total || 0) / filters.limit);
  const currentPage = Math.floor(filters.skip / filters.limit) + 1;

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">全局日志审计</h1>
        <button
          onClick={exportCSV}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
        >
          <Download size={16} /> 导出 CSV
        </button>
      </div>

      {/* 筛选表单 */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 bg-white dark:bg-neutral-800 p-4 rounded shadow">
        <input
          type="number"
          placeholder="用户ID"
          value={filters.user_id}
          onChange={(e) => handleFilterChange('user_id', e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="text"
          placeholder="模型"
          value={filters.model}
          onChange={(e) => handleFilterChange('model', e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="number"
          placeholder="状态码"
          value={filters.status_code}
          onChange={(e) => handleFilterChange('status_code', e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="datetime-local"
          placeholder="开始时间"
          value={filters.start_time}
          onChange={(e) => handleFilterChange('start_time', e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="datetime-local"
          placeholder="结束时间"
          value={filters.end_time}
          onChange={(e) => handleFilterChange('end_time', e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={() => refetch()}
          className="flex items-center justify-center gap-2 bg-primary text-white rounded px-4 py-1"
        >
          <Search size={16} /> 搜索
        </button>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto bg-white dark:bg-neutral-800 rounded shadow">
        <table className="min-w-full divide-y divide-neutral-200">
          <thead className="bg-neutral-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-4 py-2 text-left text-xs font-medium text-neutral-500 uppercase cursor-pointer hover:bg-neutral-100"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: ' ↑', desc: ' ↓' }[header.column.getIsSorted() as string] ?? ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-8">加载中...</td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-8">暂无数据</td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-neutral-50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2 text-sm">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex justify-between items-center">
        <span>共 {data?.total || 0} 条</span>
        <div className="flex gap-2">
          <button
            disabled={currentPage === 1}
            onClick={() => handlePageChange(filters.skip - filters.limit)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            上一页
          </button>
          <span className="px-3 py-1">第 {currentPage} / {totalPages} 页</span>
          <button
            disabled={currentPage === totalPages}
            onClick={() => handlePageChange(filters.skip + filters.limit)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            下一页
          </button>
        </div>
        <select
          value={filters.limit}
          onChange={(e) => handleFilterChange('limit', Number(e.target.value))}
          className="border rounded px-2 py-1"
        >
          <option value={50}>50条/页</option>
          <option value={100}>100条/页</option>
          <option value={200}>200条/页</option>
        </select>
      </div>
    </div>
  );
}