import { useState } from 'react';
import { Edit, Trash2, X, AlertTriangle } from 'lucide-react';

// 定义 API Key 数据类型（与后端对齐）
export interface APIKey {
  id: number;
  key: string;           // 脱敏后的 key（如 "sk-abc...xyz"）
  is_enabled: boolean;
  last_used_at: string | null;
  created_at: string;
}

interface KeyListTableProps {
  keys: APIKey[];
  onEdit?: (key: APIKey) => void;
  onDelete?: (id: number) => void;
}

export default function KeyListTable({ keys, onEdit, onDelete }: KeyListTableProps) {
  // 删除确认弹窗状态
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedKeyId, setSelectedKeyId] = useState<number | null>(null);

  const handleDeleteClick = (id: number) => {
    setSelectedKeyId(id);
    setDeleteModalOpen(true);
  };

  const confirmDelete = () => {
    if (selectedKeyId !== null && onDelete) {
      onDelete(selectedKeyId);
    }
    setDeleteModalOpen(false);
    setSelectedKeyId(null);
  };

  const cancelDelete = () => {
    setDeleteModalOpen(false);
    setSelectedKeyId(null);
  };

  return (
    <>
      {/* 表格容器（支持横向滚动） */}
      <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-700">
        <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
          <thead className="bg-neutral-50 dark:bg-neutral-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                API Key
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                最后使用时间
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-neutral-900 divide-y divide-neutral-200 dark:divide-neutral-700">
            {keys.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-neutral-500 dark:text-neutral-400">
                  暂无 API Key，点击上方按钮添加
                </td>
              </tr>
            ) : (
              keys.map((key) => (
                <tr key={key.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-neutral-900 dark:text-white">
                    {key.key}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        key.is_enabled
                          ? 'bg-success/10 text-success'
                          : 'bg-danger/10 text-danger'
                      }`}
                    >
                      {key.is_enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-600 dark:text-neutral-400">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleString()
                      : '从未使用'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEdit?.(key)}
                        className="p-1 text-neutral-600 hover:text-primary dark:text-neutral-400 dark:hover:text-primary rounded-md transition-colors"
                        aria-label={`编辑 Key ${key.key}`}
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteClick(key.id)}
                        className="p-1 text-neutral-600 hover:text-danger dark:text-neutral-400 dark:hover:text-danger rounded-md transition-colors"
                        aria-label={`删除 Key ${key.key}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 自定义确认弹窗（受控组件） */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-danger">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="text-lg font-semibold">确认删除</h3>
              </div>
              <button
                onClick={cancelDelete}
                className="p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-700"
                aria-label="关闭"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-neutral-700 dark:text-neutral-300 mb-6">
              确定要删除这个 API Key 吗？此操作不可撤销。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={cancelDelete}
                className="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-danger text-white rounded-md hover:bg-danger/90 transition-colors"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}