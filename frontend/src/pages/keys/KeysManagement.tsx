import { useState } from 'react';
import { useKeys, useAddKey, useDeleteKey } from '@/hooks/useKeys';
import KeyListTable from './KeyListTable';
import type { APIKey } from '@/api/types/api.types';

// 定义添加表单的数据类型
interface AddKeyFormData {
  key_value: string;
  base_url?: string;
}

export default function KeysManagement() {
  const { data: keys, isLoading, isError, error, refetch } = useKeys();
  const addKey = useAddKey();
  const deleteKey = useDeleteKey();

  // 表单状态
  const [formData, setFormData] = useState<AddKeyFormData>({
    key_value: '',
    base_url: '',
  });
  const [formErrors, setFormErrors] = useState<{ key_value?: string }>({});

  // 表单验证
  const validateForm = (): boolean => {
    const errors: { key_value?: string } = {};
    if (!formData.key_value.trim()) {
      errors.key_value = 'API Key 不能为空';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAdd = () => {
    if (!validateForm()) return;
    addKey.mutate(formData, {
      onSuccess: () => {
        setFormData({ key_value: '', base_url: '' });
        setFormErrors({});
        refetch(); // 刷新列表
      },
    });
  };

  const handleDelete = (id: number) => {
    deleteKey.mutate(id, {
      onSuccess: () => refetch(),
    });
  };

  const handleEdit = (key: APIKey) => {
    // TODO: 实现编辑功能（可打开弹窗预填表单）
    console.log('编辑 Key:', key);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">API Keys 管理</h1>

      {/* 添加 Key 表单卡片 */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">添加新 Key</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="key_value" className="block text-sm font-medium mb-1">
              API Key 值 <span className="text-danger">*</span>
            </label>
            <input
              id="key_value"
              type="text"
              placeholder="sk-xxxxxxxxxxxxxxxx"
              value={formData.key_value}
              onChange={(e) => setFormData({ ...formData, key_value: e.target.value })}
              className={`w-full px-3 py-2 border rounded-md dark:bg-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary transition-colors
                ${formErrors.key_value ? 'border-danger focus:ring-danger' : 'border-neutral-300 dark:border-neutral-600'}`}
              aria-label="API Key 值"
            />
            {formErrors.key_value && (
              <p className="mt-1 text-sm text-danger">{formErrors.key_value}</p>
            )}
          </div>

          <div>
            <label htmlFor="base_url" className="block text-sm font-medium mb-1">
              Base URL (可选)
            </label>
            <input
              id="base_url"
              type="text"
              placeholder="https://api.openai.com/v1"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md dark:bg-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary"
              aria-label="Base URL"
            />
          </div>

          <button
            onClick={handleAdd}
            disabled={addKey.isPending}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {addKey.isPending ? '添加中...' : '添加 Key'}
          </button>
        </div>
      </div>

      {/* Key 列表表格（使用可复用组件，含删除确认弹窗） */}
      {isLoading ? (
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-8 text-center text-neutral-500">
          加载中...
        </div>
      ) : isError ? (
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-8 text-center">
          <p className="text-danger mb-2">加载失败: {(error as Error)?.message || '未知错误'}</p>
          <button onClick={() => refetch()} className="text-primary hover:underline text-sm">点击重试</button>
        </div>
      ) : (
        <KeyListTable
          keys={keys || []}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}