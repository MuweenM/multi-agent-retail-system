import { useState, useEffect } from 'react';
import LoginPage from './components/app/LoginPage';
import Dashboard from './components/app/dashboard/Dashboard';
import AnalyticsPage from './components/app/AnalyticsPage';
import SubmitReturnPage from './components/app/SubmitReturnPage';
import BulkJobPage from './components/app/BulkJobPage';
import UsagePage from './components/app/UsagePage';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Avatar, AvatarFallback, AvatarBadge } from './components/ui/avatar';
import {
  LayoutDashboard,
  BrainCircuit,
  FileText,
  Upload,
  BarChart2,
  LogOut,
  AlertCircle,
  X,
} from 'lucide-react';
import { getCurrentUser, logout, onUpgradeNotice } from './lib/api';
import type { AuthUser } from './types/contracts';

type View = 'dashboard' | 'analytics' | 'submit' | 'bulk' | 'usage';

// ── Nav item config ───────────────────────────────────────────────────────────
interface NavItem {
  id: View;
  label: string;
  icon: React.ReactNode;
  roles: string[];
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <LayoutDashboard className="h-3.5 w-3.5" />,
    roles: ['viewer', 'reviewer', 'admin'],
  },
  {
    id: 'submit',
    label: 'Submit Return',
    icon: <FileText className="h-3.5 w-3.5" />,
    roles: ['reviewer', 'admin'],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: <BrainCircuit className="h-3.5 w-3.5" />,
    roles: ['viewer', 'reviewer', 'admin'],
  },
  {
    id: 'bulk',
    label: 'Bulk Jobs',
    icon: <Upload className="h-3.5 w-3.5" />,
    roles: ['reviewer', 'admin'],
  },
  {
    id: 'usage',
    label: 'Usage',
    icon: <BarChart2 className="h-3.5 w-3.5" />,
    roles: ['admin'],
  },
];

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<AuthUser | null>(getCurrentUser());
  const [view, setView] = useState<View>('dashboard');
  const [upgradeNotice, setUpgradeNotice] = useState<string | null>(null);

  // Register upgrade notice callback once
  useEffect(() => {
    onUpgradeNotice((msg) => setUpgradeNotice(msg));
  }, []);

  // Hash-based routing: #/login redirects to login
  useEffect(() => {
    const onHash = () => {
      if (window.location.hash === '#/login') setUser(null);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const handleLogin = () => {
    setUser(getCurrentUser());
    window.location.hash = '';
  };

  const handleLogout = () => {
    logout();
    setUser(null);
  };

  // Unauthenticated state
  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Filter nav items by role
  const visibleNavItems = NAV_ITEMS.filter((n) => n.roles.includes(user.role));

  // Ensure current view is accessible; if not, fall back to first accessible
  const currentView = visibleNavItems.find((n) => n.id === view)
    ? view
    : (visibleNavItems[0]?.id ?? 'dashboard');

  const renderPage = () => {
    switch (currentView) {
      case 'analytics':
        return <AnalyticsPage />;
      case 'submit':
        return <SubmitReturnPage />;
      case 'bulk':
        return <BulkJobPage />;
      case 'usage':
        return <UsagePage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Upgrade notice banner */}
      {upgradeNotice && (
        <div className="flex items-center justify-between gap-3 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
            {upgradeNotice}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setUpgradeNotice(null)}
            className="h-5 w-5 rounded-full text-amber-600 hover:bg-amber-100"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}

      {/* Top Navigation */}
      <nav className="sticky top-0 z-40 w-full border-b border-neutral-200 bg-white/95 backdrop-blur-sm">
        <div className="h-13 mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-2 sm:px-6 lg:px-8">
          {/* Brand */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-black text-xs font-bold text-white">
                R
              </div>
              <span className="text-sm font-semibold tracking-tight text-neutral-950">
                ReturnIQ
              </span>
              <Badge
                variant="outline"
                className="rounded-full border-neutral-200 bg-neutral-100 px-2 py-0 font-mono text-[10px] text-neutral-500"
              >
                v1.1
              </Badge>
            </div>

            {/* Nav Pills */}
            <div className="hidden items-center gap-1 md:flex">
              {visibleNavItems.map((item) => {
                const isActive = currentView === item.id;
                return (
                  <Button
                    key={item.id}
                    id={`nav-${item.id}`}
                    variant={isActive ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setView(item.id)}
                    className={`h-7 rounded-full px-3 text-xs font-medium ${
                      isActive
                        ? 'bg-black text-white hover:bg-neutral-800'
                        : 'text-neutral-600 hover:bg-neutral-100 hover:text-black'
                    }`}
                  >
                    {item.icon}
                    <span className="ml-1.5">{item.label}</span>
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Right: User info + logout */}
          <div className="flex items-center gap-3">
            <div className="hidden flex-col items-end sm:flex">
              <span className="font-mono text-[11px] font-medium text-neutral-700">
                {user.sub}
              </span>
              <Badge
                variant="outline"
                className="rounded-full border-neutral-200 bg-neutral-100 px-1.5 py-0 font-mono text-[9px] uppercase tracking-wider text-neutral-500"
              >
                {user.role}
              </Badge>
            </div>
            <Avatar size="sm" className="border border-neutral-200">
              <AvatarFallback className="bg-neutral-100 font-mono text-[11px] font-semibold text-neutral-900">
                {user.sub.slice(0, 2).toUpperCase()}
              </AvatarFallback>
              <AvatarBadge className="bg-emerald-500" />
            </Avatar>
            <Button
              id="nav-logout"
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="h-8 w-8 rounded-full text-neutral-500 hover:text-rose-600"
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">{renderPage()}</main>
    </div>
  );
}
