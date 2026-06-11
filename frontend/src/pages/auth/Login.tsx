import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginPage from './LoginPage';
import { useAuthStore } from '@/stores/authStore';
import { AxiosError } from 'axios';

interface LoginFormData {
  username: string;
  password: string;
  rememberMe: boolean;
}

export default function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const [serverError, setServerError] = useState('');

  const handleLogin = async (data: LoginFormData) => {
    setServerError('');
    try {
      await login({ username: data.username, password: data.password });
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof AxiosError) {
        setServerError(err.response?.data?.detail || '登录失败，请检查用户名和密码');
      } else {
        setServerError('登录失败，请稍后再试');
      }
    }
  };

  return <LoginPage isLoading={isLoading} onSubmit={handleLogin} serverError={serverError} />;
}
