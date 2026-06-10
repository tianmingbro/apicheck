import { Outlet, Link, useNavigate } from 'react-router-dom';

export default function DashboardLayout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700">
        <div className="p-6">
          <h1 className="text-xl font-bold text-primary-600">API Farm</h1>
        </div>
        <nav className="mt-6">
          <NavItem to="/dashboard">Dashboard</NavItem>
          <NavItem to="/keys">API Keys</NavItem>
          <NavItem to="/usage">Usage</NavItem>
          <NavItem to="/billing">Billing</NavItem>
        </nav>
        <div className="absolute bottom-6 left-6">
          <button onClick={handleLogout} className="text-danger hover:underline">
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="block px-6 py-2 hover:bg-primary-50 dark:hover:bg-neutral-700"
    >
      {children}
    </Link>
  );
}