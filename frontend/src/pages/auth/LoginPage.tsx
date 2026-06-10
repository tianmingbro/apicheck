import { useState, FormEvent } from 'react';

interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface LoginPageProps {
  isLoading?: boolean;
  onSubmit: (data: LoginFormData) => void;
  serverError?: string; // 可选，用于展示全局错误（如“用户名或密码错误”）
}

export default function LoginPage({ isLoading = false, onSubmit, serverError }: LoginPageProps) {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [touched, setTouched] = useState<{ email: boolean; password: boolean }>({
    email: false,
    password: false,
  });

  // 简单的表单验证
  const errors: Partial<LoginFormData & { emailFormat?: string }> = {};
  if (touched.email && !formData.email) {
    errors.email = '邮箱不能为空';
  } else if (touched.email && !/\S+@\S+\.\S+/.test(formData.email)) {
    errors.emailFormat = '请输入有效的邮箱地址';
  }
  if (touched.password && !formData.password) {
    errors.password = '密码不能为空';
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // 标记所有字段为已触碰以显示验证错误
    setTouched({ email: true, password: true });
    if (formData.email && formData.password) {
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
          登录
        </h1>

        <form onSubmit={handleSubmit} noValidate>
          {/* 邮箱输入框 */}
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              邮箱
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              onBlur={() => handleBlur('email')}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary transition-colors
                ${errors.email || errors.emailFormat
                  ? 'border-danger focus:ring-danger'
                  : 'border-neutral-300 dark:border-neutral-600'
                }
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              aria-label="邮箱地址"
            />
            {/* 验证错误反馈 */}
            {(errors.email || errors.emailFormat) && (
              <p className="mt-1 text-sm text-danger" role="alert">
                {errors.email || errors.emailFormat}
              </p>
            )}
          </div>

          {/* 密码输入框 */}
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
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary transition-colors
                ${errors.password
                  ? 'border-danger focus:ring-danger'
                  : 'border-neutral-300 dark:border-neutral-600'
                }
                bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              aria-label="密码"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-danger" role="alert">
                {errors.password}
              </p>
            )}
          </div>

          {/* 记住我选项 */}
          <div className="flex items-center justify-between mb-6">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.rememberMe}
                onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                disabled={isLoading}
                className="w-4 h-4 text-primary focus:ring-primary border-neutral-300 rounded"
                aria-label="记住我"
              />
              <span className="ml-2 text-sm text-neutral-700 dark:text-neutral-300">
                记住我
              </span>
            </label>
            {/* 预留“忘记密码”链接位置（可后续添加） */}
            <button
              type="button"
              className="text-sm text-primary hover:underline focus:outline-none"
              aria-label="忘记密码"
            >
              忘记密码？
            </button>
          </div>

          {/* 服务器错误反馈 */}
          {serverError && (
            <div className="mb-4 p-2 bg-danger/10 border border-danger/30 rounded text-danger text-sm text-center" role="alert">
              {serverError}
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-primary text-white font-semibold rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="登录"
          >
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        {/* 注册引导 */}
        <p className="mt-6 text-center text-sm text-neutral-600 dark:text-neutral-400">
          还没有账号？{' '}
          <a href="/register" className="text-primary hover:underline" aria-label="前往注册">
            立即注册
          </a>
        </p>
      </div>
    </div>
  );
}