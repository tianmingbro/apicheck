import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';

interface LoginFormData {
  username: string;
  password: string;
  rememberMe: boolean;
}

interface LoginPageProps {
  isLoading?: boolean;
  onSubmit: (data: LoginFormData) => void;
  serverError?: string;
}

export default function LoginPage({ isLoading = false, onSubmit, serverError }: LoginPageProps) {
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
    rememberMe: false,
  });

  const [touched, setTouched] = useState<{ username: boolean; password: boolean }>({
    username: false,
    password: false,
  });

  const errors: Partial<{ username: string; password: string }> = {};
  if (touched.username && !formData.username) {
    errors.username = '用户名不能为空';
  }
  if (touched.password && !formData.password) {
    errors.password = '密码不能为空';
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setTouched({ username: true, password: true });
    if (formData.username && formData.password) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof LoginFormData, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleBlur = (field: keyof typeof touched) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900 p-4">
      <div className="w-full max-w-md bg-white dark:bg-neutral-800 rounded-lg shadow-md p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-center text-neutral-900 dark:text-white mb-6">
          KEYPILOT 登录
        </h1>

        <form onSubmit={handleSubmit} noValidate>
          {/* 用户名 */}
          <div className="mb-4">
            <label htmlFor="username" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              用户名
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              onBlur={() => handleBlur('username')}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors
                ${errors.username
                  ? 'border-danger focus:ring-danger'
                  : 'border-neutral-300 dark:border-neutral-600'
                }
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              placeholder="请输入用户名"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-danger" role="alert">{errors.username}</p>
            )}
          </div>

          {/* 密码 */}
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              密码
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors
                ${errors.password
                  ? 'border-danger focus:ring-danger'
                  : 'border-neutral-300 dark:border-neutral-600'
                }
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              placeholder="请输入密码"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-danger" role="alert">{errors.password}</p>
            )}
          </div>

          {/* 记住我 */}
          <div className="flex items-center justify-between mb-6">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.rememberMe}
                onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                disabled={isLoading}
                className="w-4 h-4 text-primary-500 focus:ring-primary-500 border-neutral-300 rounded"
              />
              <span className="ml-2 text-sm text-neutral-700 dark:text-neutral-300">记住我</span>
            </label>
          </div>

          {/* 服务器错误 */}
          {serverError && (
            <div className="mb-4 p-2 bg-danger/10 border border-danger/30 rounded text-danger text-sm text-center" role="alert">
              {serverError}
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-primary-500 text-white font-semibold rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        {/* 注册引导 */}
        <p className="mt-6 text-center text-sm text-neutral-600 dark:text-neutral-400">
          还没有账号？{' '}
          <Link to="/register" className="text-primary-500 hover:underline">
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}
