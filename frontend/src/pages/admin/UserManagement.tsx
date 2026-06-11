import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, type AdminUser } from '@/services/modules/adminApi';
import { Pencil, Trash2, X, AlertTriangle } from 'lucide-react';

export default function UserManagement() {
  const qc = useQueryClient();
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [editForm, setEditForm] = useState({ quota_limit: 0, extra_tokens: 0, role: '' });
  const [deleteConfirm, setDeleteConfirm] = useState<AdminUser | null>(null);

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers().then((r) => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { quota_limit?: number; extra_tokens?: number; role?: string } }) =>
      adminApi.updateUser(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      setEditingUser(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminApi.deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      setDeleteConfirm(null);
    },
  });

  const openEdit = (user: AdminUser) => {
    setEditingUser(user);
    setEditForm({ quota_limit: user.quota_limit, extra_tokens: user.extra_tokens, role: user.role });
  };

  const handleSave = () => {
    if (!editingUser) return;
    updateMutation.mutate({ id: editingUser.id, data: editForm });
  };

  if (isLoading) return <div className="p-6 text-center">加载中...</div>;
  if (error) return <div className="p-6 text-danger">加载失败: {(error as Error).message}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">用户管理</h1>

      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
          <thead className="bg-neutral-50 dark:bg-neutral-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">用户名</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">角色</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">已用/配额</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">额外Token</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">注册时间</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
            {(users || []).map((user) => (
              <tr key={user.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-700/50">
                <td className="px-4 py-3 text-sm">{user.id}</td>
                <td className="px-4 py-3 text-sm font-medium">{user.username}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${user.role === 'admin' ? 'bg-primary/10 text-primary' : 'bg-neutral-100 text-neutral-600'}`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">{user.quota_used.toLocaleString()} / {user.quota_limit.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm">{user.extra_tokens.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-neutral-500">{new Date(user.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-sm text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => openEdit(user)} className="p-1 hover:text-primary" title="编辑">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => setDeleteConfirm(user)} className="p-1 hover:text-danger" title="删除">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">编辑用户: {editingUser.username}</h3>
              <button onClick={() => setEditingUser(null)} className="p-1 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">角色</label>
                <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className="w-full border rounded px-3 py-2 dark:bg-neutral-700">
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">配额上限</label>
                <input type="number" value={editForm.quota_limit}
                  onChange={(e) => setEditForm({ ...editForm, quota_limit: Number(e.target.value) })}
                  className="w-full border rounded px-3 py-2 dark:bg-neutral-700" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">额外 Token</label>
                <input type="number" value={editForm.extra_tokens}
                  onChange={(e) => setEditForm({ ...editForm, extra_tokens: Number(e.target.value) })}
                  className="w-full border rounded px-3 py-2 dark:bg-neutral-700" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setEditingUser(null)}
                className="px-4 py-2 border rounded-md hover:bg-neutral-50 dark:hover:bg-neutral-700">取消</button>
              <button onClick={handleSave} disabled={updateMutation.isPending}
                className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50">
                {updateMutation.isPending ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirm modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center gap-2 text-danger mb-4">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="text-lg font-semibold">确认删除</h3>
            </div>
            <p>确定要删除用户 "{deleteConfirm.username}" 吗？此操作不可撤销。</p>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border rounded-md hover:bg-neutral-50 dark:hover:bg-neutral-700">取消</button>
              <button onClick={() => deleteMutation.mutate(deleteConfirm.id)}
                className="px-4 py-2 bg-danger text-white rounded-md hover:bg-danger/90">确认删除</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
