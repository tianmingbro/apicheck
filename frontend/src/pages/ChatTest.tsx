import { useState, FormEvent } from 'react';
import { Send, Clock, Cpu } from 'lucide-react';
import apiClient from '@/services/apiClient';

const MODELS = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4o-mini'];

interface ChatResult {
  content: string;
  model: string;
  durationMs: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export default function ChatTest() {
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<ChatResult[]>([]);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    setError('');
    const start = performance.now();

    try {
      const resp = await apiClient.post('/api/chat/completions', {
        model,
        messages: [{ role: 'user', content: message.trim() }],
      });

      const data = resp.data;
      const durationMs = Math.round(performance.now() - start);

      setResults(prev => [{
        content: data.choices?.[0]?.message?.content || JSON.stringify(data),
        model,
        durationMs,
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      }, ...prev]);

      setMessage('');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(axiosErr.response?.data?.detail || axiosErr.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">聊天测试</h1>
      <p className="text-sm text-neutral-500">测试你的 API Key 是否正常工作</p>

      {/* Input form */}
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <form onSubmit={handleSend} className="space-y-4">
          <div>
            <label htmlFor="model-select" className="block text-sm font-medium mb-1">
              模型
            </label>
            <select
              id="model-select"
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full md:w-64 px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md bg-white dark:bg-neutral-700 text-sm"
            >
              {MODELS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="chat-message" className="block text-sm font-medium mb-1">
              消息
            </label>
            <textarea
              id="chat-message"
              value={message}
              onChange={e => setMessage(e.target.value)}
              rows={3}
              placeholder="输入测试消息..."
              className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md bg-white dark:bg-neutral-700 resize-y"
              disabled={loading}
            />
          </div>

          {error && (
            <div className="p-3 bg-danger/10 border border-danger/30 rounded text-danger text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            {loading ? '发送中...' : '发送'}
          </button>
        </form>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
            返回结果 ({results.length})
          </h2>
          {results.map((r, i) => (
            <div key={i} className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
              <div className="flex flex-wrap items-center gap-3 mb-3 text-sm text-neutral-500">
                <span className="flex items-center gap-1">
                  <Cpu className="w-3.5 h-3.5" /> {r.model}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> {r.durationMs}ms
                </span>
                <span>Prompt: {r.promptTokens}</span>
                <span>Completion: {r.completionTokens}</span>
                <span className="font-semibold text-neutral-700 dark:text-neutral-300">
                  Total: {r.totalTokens} tokens
                </span>
              </div>
              <div className="p-4 bg-neutral-50 dark:bg-neutral-900 rounded-md whitespace-pre-wrap text-sm text-neutral-900 dark:text-white">
                {r.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
