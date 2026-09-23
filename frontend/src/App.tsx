import { useState } from 'react';
import Dashboard from './components/app/dashboard/Dashboard';
import AnalyticsPage from './components/app/AnalyticsPage';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { LayoutDashboard, BrainCircuit } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'analytics'>('analytics');

  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Top Global Navigation Switcher */}
      <nav className="border-b border-neutral-200 bg-neutral-50/80 px-4 py-2 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
              Retail Intelligence Suite
            </span>
            <Badge variant="outline" className="rounded-full border-neutral-200 bg-white font-mono text-[10px]">
              Multi-Agent v1.1
            </Badge>
          </div>

          <div className="flex items-center gap-1.5 rounded-full border border-neutral-200 bg-white p-1 shadow-xs">
            <Button
              variant={currentView === 'analytics' ? 'default' : 'ghost'}
              size="sm"
              className={`h-7 rounded-full px-3 text-xs font-medium ${
                currentView === 'analytics'
                  ? 'bg-black text-white hover:bg-neutral-800'
                  : 'text-neutral-600 hover:bg-neutral-100'
              }`}
              onClick={() => setCurrentView('analytics')}
            >
              <BrainCircuit className="mr-1.5 size-3.5" />
              Agent 2 Analytics
            </Button>
            <Button
              variant={currentView === 'dashboard' ? 'default' : 'ghost'}
              size="sm"
              className={`h-7 rounded-full px-3 text-xs font-medium ${
                currentView === 'dashboard'
                  ? 'bg-black text-white hover:bg-neutral-800'
                  : 'text-neutral-600 hover:bg-neutral-100'
              }`}
              onClick={() => setCurrentView('dashboard')}
            >
              <LayoutDashboard className="mr-1.5 size-3.5" />
              Returns Dashboard
            </Button>
          </div>
        </div>
      </nav>

      {/* Main View Container */}
      <div className="flex-1">
        {currentView === 'analytics' ? <AnalyticsPage /> : <Dashboard />}
      </div>
    </div>
  );
}
