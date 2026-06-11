import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '@/services/modules/authApi';
import { AxiosError } from 'axios';

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const errors: Record<string, string> = {};
  if (touched.username && !username.trim()) errors.username = '用户名不能为空';
  if (touched.password && !password) errors.password = '密码不能为空';
  if (touched.password && password.length < 6) errors.password = '密码至少6个字符';
  if (touched.confirmPassword && password !== confirmPassword) errors.confirmPassword = '两次密码不一致';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched({ username: true, password: true, confirmPassword: true });
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    setError('');
    try {
      await authApi.register({ username: username.trim(), password });
      // Registration successful — redirect to login
      navigate('/login', { state: { registered: true } });
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail || '注册失败，请稍后再试');
      } else {
        setError('注册失败，请稍后再试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900 p-4">
      <div className="w-full max-w-md bg-white dark:bg-neutral-800 rounded-lg shadow-md p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-center text-neutral-900 dark:text-white mb-6">
          注册 KEYPILOT
        </h1>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label htmlFor="reg-username" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              用户名
            </label>
            <input
              id="reg-username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onBlur={() => setTouched((p) => ({ ...p, username: true }))}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors
                ${errors.username ? 'border-danger' : 'border-neutral-300 dark:border-neutral-600'}
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white disabled:opacity-50`}
              placeholder="请输入用户名"
            />
            {errors.username && <p className="mt-1 text-sm text-danger">{errors.username}</p>}
          </div>

          <div className="mb-4">
            <label htmlFor="reg-password" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              密码
            </label>
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((p) => ({ ...p, password: true }))}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors
                ${errors.password ? 'border-danger' : 'border-neutral-300 dark:border-neutral-600'}
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white disabled:opacity-50`}
              placeholder="至少6个字符"
            />
            {errors.password && <p className="mt-1 text-sm text-danger">{errors.password}</p>}
          </div>

          <div className="mb-6">
            <label htmlFor="reg-confirm" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              确认密码
            </label>
            <input
              id="reg-confirm"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onBlur={() => setTouched((p) => ({ ...p, confirmPassword: true }))}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors
                ${errors.confirmPassword ? 'border-danger' : 'border-neutral-300 dark:border-neutral-600'}
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white disabled:opacity-50`}
              placeholder="再次输入密码"
            />
            {errors.confirmPassword && <p className="mt-1 text-sm text-danger">{errors.confirmPassword}</p>}
          </div>

          {error && (
            <div className="mb-4 p-2 bg-danger/10 border border-danger/30 rounded text-danger text-sm text-center" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-primary-500 text-white font-semibold rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:opacity-50"
          >
            {isLoading ? '注册中...' : '注册'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-neutral-600 dark:text-neutral-400">
          已有账号？{' '}
          <Link to="/login" className="text-primary-500 hover:underline">
            立即登录
          </Link>
        </p>
      </div>
    </div>
  );
}
