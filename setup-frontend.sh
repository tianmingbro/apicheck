#!/bin/bash
# setup-frontend.sh - 在 my-api-farm 根目录执行

set -e  # 出错即停

echo "📦 创建前端项目目录..."
mkdir -p frontend
cd frontend

echo "📄 生成 package.json..."
cat > package.json << 'EOF'
{
  "name": "api-farm-dashboard",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.28.4",
    "axios": "^1.6.8",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/node": "^20.11.30",
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@typescript-eslint/eslint-plugin": "^7.2.0",
    "@typescript-eslint/parser": "^7.2.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.6",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
EOF

echo "📄 生成 TypeScript 配置..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

cat > tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
EOF

echo "📄 生成 Vite 配置..."
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
EOF

echo "📄 生成 Tailwind 配置..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          500: '#8b5cf6',
          600: '#7c3aed',
        },
        danger: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
        neutral: {
          50: '#f9fafb',
          100: '#f3f4f6',
          800: '#1f2937',
          900: '#111827',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
EOF

echo "📄 生成 PostCSS 配置..."
cat > postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF

echo "📄 生成环境变量示例..."
cat > .env.example << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=API Farm Dashboard
EOF

echo "📄 生成 index.html..."
cat > index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>API Farm Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

echo "📁 创建 src 目录结构..."
mkdir -p src/{api/endpoints,api/types,assets,components/{common,layout,features},hooks,layouts,pages,routes,store,styles,types,utils}

echo "📄 生成 src/main.tsx..."
cat > src/main.tsx << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

echo "📄 生成 src/App.tsx..."
cat > src/App.tsx << 'EOF'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import KeysManagement from './pages/KeysManagement';
import Usage from './pages/Usage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/keys" element={<KeysManagement />} />
            <Route path="/usage" element={<Usage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
EOF

echo "📄 生成全局样式..."
cat > src/styles/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-neutral-50 text-neutral-900 dark:bg-neutral-900 dark:text-neutral-50;
  }
}
EOF

echo "📄 生成 Axios 客户端..."
cat > src/api/client.ts << 'EOF'
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
EOF

echo "📄 生成 API 类型定义..."
cat > src/api/types/api.types.ts << 'EOF'
export interface APIKey {
  id: number;
  key: string;
  base_url?: string;
  is_enabled: boolean;
  created_at: string;
  total_calls: number;
  last_used_at?: string;
}

export interface CreateKeyPayload {
  key_value: string;
  base_url?: string;
}

export interface User {
  id: number;
  username: string;
  role: string;
}

export interface UsageStats {
  total_calls: number;
  total_tokens: number;
  remaining_quota: number;
}
EOF

echo "📄 生成认证 API 端点..."
cat > src/api/endpoints/auth.ts << 'EOF'
import client from '../client';

export const authApi = {
  login: (username: string, password: string) =>
    client.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
  register: (username: string, password: string) =>
    client.post('/auth/register', { username, password }),
};
EOF

echo "📄 生成 Keys API 端点..."
cat > src/api/endpoints/keys.ts << 'EOF'
import client from '../client';
import type { APIKey, CreateKeyPayload } from '@/api/types/api.types';

export const keysApi = {
  list: () => client.get<APIKey[]>('/keys/'),
  create: (data: CreateKeyPayload) => client.post<APIKey>('/keys/', data),
  delete: (id: number) => client.delete(`/keys/${id}`),
};
EOF

echo "📄 生成统计 API 端点..."
cat > src/api/endpoints/stats.ts << 'EOF'
import client from '../client';
import type { UsageStats } from '@/api/types/api.types';

export const statsApi = {
  getUsage: () => client.get<UsageStats>('/stats/usage'),
};
EOF

echo "📄 生成认证 Store..."
cat > src/store/authStore.ts << 'EOF'
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      isAuthenticated: false,
      setToken: (token) => set({ token, isAuthenticated: true }),
      logout: () => set({ token: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);
EOF

echo "📄 生成自定义 Hooks..."
cat > src/hooks/useAuth.ts << 'EOF'
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/api/endpoints/auth';
import { useAuthStore } from '@/store/authStore';

export const useLogin = () => {
  const setToken = useAuthStore((s) => s.setToken);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (data) => {
      setToken(data.data.access_token);
      navigate('/dashboard');
    },
  });
};

export const useLogout = () => {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  return () => {
    logout();
    navigate('/login');
  };
};
EOF

cat > src/hooks/useKeys.ts << 'EOF'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { keysApi } from '@/api/endpoints/keys';
import type { CreateKeyPayload } from '@/api/types/api.types';

export const useKeys = () => {
  return useQuery({
    queryKey: ['keys'],
    queryFn: () => keysApi.list().then((res) => res.data),
  });
};

export const useAddKey = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateKeyPayload) => keysApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['keys'] }),
  });
};

export const useDeleteKey = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => keysApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['keys'] }),
  });
};
EOF

echo "📄 生成工具函数..."
cat > src/utils/maskApiKey.ts << 'EOF'
export const maskApiKey = (key: string): string => {
  if (key.length <= 8) return '*'.repeat(key.length);
  return key.slice(0, 4) + '*'.repeat(key.length - 8) + key.slice(-4);
};
EOF

cat > src/utils/formatDate.ts << 'EOF'
export const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString();
};
EOF

echo "📄 生成布局组件..."
cat > src/layouts/DashboardLayout.tsx << 'EOF'
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';

const DashboardLayout = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useLogout();
  const navigate = useNavigate();

  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      <nav className="bg-white dark:bg-neutral-800 shadow-sm border-b border-neutral-200 dark:border-neutral-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <Link to="/dashboard" className="inline-flex items-center px-1 pt-1 text-sm font-medium">Dashboard</Link>
              <Link to="/keys" className="inline-flex items-center px-1 pt-1 text-sm font-medium">API Keys</Link>
              <Link to="/usage" className="inline-flex items-center px-1 pt-1 text-sm font-medium">Usage</Link>
            </div>
            <button onClick={logout} className="text-sm text-red-600 hover:text-red-800">Logout</button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
EOF

echo "📄 生成页面组件..."
cat > src/pages/Login.tsx << 'EOF'
import { useState } from 'react';
import { useLogin } from '@/hooks/useAuth';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const loginMutation = useLogin();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900">
      <div className="bg-white dark:bg-neutral-800 p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6">API Farm Dashboard</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 border rounded-md mb-4 dark:bg-neutral-700"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border rounded-md mb-4 dark:bg-neutral-700"
            required
          />
          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full bg-primary-500 text-white py-2 rounded-md hover:bg-primary-600 disabled:opacity-50"
          >
            {loginMutation.isPending ? 'Logging in...' : 'Login'}
          </button>
          {loginMutation.isError && (
            <p className="text-red-500 text-sm mt-2">Login failed. Check credentials.</p>
          )}
        </form>
      </div>
    </div>
  );
};

export default Login;
EOF

cat > src/pages/Dashboard.tsx << 'EOF'
import { useKeys } from '@/hooks/useKeys';
import { maskApiKey } from '@/utils/maskApiKey';

const Dashboard = () => {
  const { data: keys, isLoading } = useKeys();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-2">Your API Keys</h2>
        {isLoading && <p>Loading...</p>}
        {!isLoading && (!keys || keys.length === 0) && <p>No API keys added yet.</p>}
        {keys && keys.length > 0 && (
          <ul className="divide-y">
            {keys.map((key) => (
              <li key={key.id} className="py-2 flex justify-between">
                <span className="font-mono">{maskApiKey(key.key)}</span>
                <span className="text-sm text-neutral-500">
                  Calls: {key.total_calls}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
EOF

cat > src/pages/KeysManagement.tsx << 'EOF'
import { useState } from 'react';
import { useKeys, useAddKey, useDeleteKey } from '@/hooks/useKeys';
import { maskApiKey } from '@/utils/maskApiKey';

const KeysManagement = () => {
  const { data: keys, refetch } = useKeys();
  const addKey = useAddKey();
  const deleteKey = useDeleteKey();
  const [newKey, setNewKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');

  const handleAdd = () => {
    if (!newKey.trim()) return;
    addKey.mutate({ key_value: newKey, base_url: baseUrl || undefined });
    setNewKey('');
    setBaseUrl('');
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Manage API Keys</h1>
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Add New Key</h2>
        <div className="space-y-3">
          <input
            type="text"
            placeholder="API Key Value"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            className="w-full px-3 py-2 border rounded-md dark:bg-neutral-700"
          />
          <input
            type="text"
            placeholder="Base URL (optional)"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="w-full px-3 py-2 border rounded-md dark:bg-neutral-700"
          />
          <button
            onClick={handleAdd}
            disabled={addKey.isPending}
            className="bg-primary-500 text-white px-4 py-2 rounded-md hover:bg-primary-600"
          >
            {addKey.isPending ? 'Adding...' : 'Add Key'}
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-neutral-200">
          <thead className="bg-neutral-50 dark:bg-neutral-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase">Key</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase">Base URL</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase">Calls</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {keys?.map((key) => (
              <tr key={key.id}>
                <td className="px-6 py-4 font-mono text-sm">{maskApiKey(key.key)}</td>
                <td className="px-6 py-4 text-sm">{key.base_url || '-'}</td>
                <td className="px-6 py-4 text-sm">{key.total_calls}</td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => deleteKey.mutate(key.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default KeysManagement;
EOF

cat > src/pages/Usage.tsx << 'EOF'
const Usage = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Usage Statistics</h1>
      <div className="bg-white dark:bg-neutral-800 rounded-lg shadow p-6">
        <p>Charts and usage details will appear here.</p>
      </div>
    </div>
  );
};

export default Usage;
EOF

echo "📄 生成路由配置..."
cat > src/routes/index.tsx << 'EOF'
import { createBrowserRouter } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import KeysManagement from '@/pages/KeysManagement';
import Usage from '@/pages/Usage';

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    element: <DashboardLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/keys', element: <KeysManagement /> },
      { path: '/usage', element: <Usage /> },
    ],
  },
]);
EOF

echo "📄 生成 .gitignore"
cat > .gitignore << 'EOF'
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
EOF

echo "✅ 前端项目生成完成！"
echo ""
echo "接下来请执行："
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo ""
echo "同时确保后端服务已启动，并配置好 CORS 允许 http://localhost:5173"