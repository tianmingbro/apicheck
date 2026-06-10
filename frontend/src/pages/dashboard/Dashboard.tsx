// src/pages/dashboard/Dashboard.tsx
import { useEffect, useState } from 'react';
import apiClient from '@/services/apiClient';

export default function Dashboard() {
  const [message, setMessage] = useState('');

  const testApi = async () => {
    try {
      // 示例：调用一个公开的健康检查接口（无需 token）
      const response = await apiClient.get('/health');
      setMessage(`API 响应: ${JSON.stringify(response.data)}`);
    } catch (err) {
      console.error(err);
      setMessage('请求失败，请查看控制台');
    }
  };

  useEffect(() => {
    testApi();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="mt-4 text-gray-600">{message || '加载中...'}</p>
      <button
        onClick={testApi}
        className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
      >
        重新测试 API
      </button>
    </div>
  );
}