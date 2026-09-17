import { useEffect, useState } from 'react';
import Dashboard from './components/app/dashboard/Dashboard';
import DesignShowcase from './components/app/dashboard/DesignShowcase';

export default function App() {
  const [page, setPage] = useState(window.location.hash);

  useEffect(() => {
    const onHashChange = () => setPage(window.location.hash);
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  if (page === '#/design') return <DesignShowcase />;
  return <Dashboard />;
}
