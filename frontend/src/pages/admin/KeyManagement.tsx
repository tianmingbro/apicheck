import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/services/modules/adminApi';
import { ToggleLeft, ToggleRight, Search } from 'lucide-react';

export default function KeyManagement() {
  const qc = useQueryClient();
  const [filterUserId, setFilterUserId] = useState('');

  const { data: keys, isLoading, error } = useQuery({
    queryKey: ['admin-keys', filterUserId],
    queryFn: () =>
      adminApi.listAllKeys(0, 200, filterUserId ? Number(filterUserId) : undefined).then((r) => r.data),
  });

  const toggleMutation = useMutation({
    mutationFn: (keyId: number) => adminApi.toggleKey(keyId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-keys'] }),
  });

  if (isLoading) return <div className="p-6 text-center">加载中...</div>;
  if (error) return <div className="p-6 text-danger">加载失败: {(error as Error).message}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">API Key 管理</h1>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <Search className="w-4 h-4 text-neutral-400" />
        <input
          type="number"
          placeholder="按用户ID筛选..."
          value={filterUserId}
          onChange={(e) => setFilterUserId(e.target.value)}
          className="border rounded px-3 py-2 text-sm w-48 dark:bg-neutral-700"
        />
        {filterUserId && (
          <button onClick={() => setFilterUserId('')} className="text-sm text-neutral-500 hover:text-neutral-700">清除</button>
        )}
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
          <thead className="bg-neutral-50 dark:bg-neutral-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">用户ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Key (加密)</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">状态</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">调用次数</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">最后使用</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
            {(keys || []).length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-neutral-500">暂无 API Key</td>
              </tr>
            ) : (
              (keys || []).map((key) => (
                <tr key={key.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-700/50">
                  <td className="px-4 py-3 text-sm">{key.id}</td>
                  <td className="px-4 py-3 text-sm">{key.user_id}</td>
                  <td className="px-4 py-3 text-sm font-mono max-w-[200px] truncate" title={key.key_value}>
                    {key.key_value.slice(0, 30)}...
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${key.is_enabled ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                      {key.is_enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{key.total_calls.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-neutral-500">
                    {key.last_used_at ? new Date(key.last_used_at).toLocaleString() : '从未使用'}
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    <button
                      onClick={() => toggleMutation.mutate(key.id)}
                      disabled={toggleMutation.isPending}
                      className={`p-1 rounded transition-colors ${key.is_enabled ? 'hover:text-danger' : 'hover:text-success'}`}
                      title={key.is_enabled ? '禁用' : '启用'}
                    >
                      {key.is_enabled ? <ToggleRight className="w-5 h-5 text-success" /> : <ToggleLeft className="w-5 h-5 text-neutral-400" />}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
