import { Suspense, useEffect } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import BottomNav from './BottomNav';
import GlobalSearch from './GlobalSearch';
import NotificationBell from './NotificationBell';
import { LeafMark } from './Logo';
import { ErrorBoundary, PageLoader } from './Feedback';
import { useAuth } from '../context/AuthContext';
import { useAppData } from '../context/AppDataContext';
import { initials } from '../utils/helpers';

export function Avatar({ name, src, size = 40 }) {
  return src ? (
    <img className="avatar" src={src} alt={name} style={{ width: size, height: size }} />
  ) : (
    <span className="avatar avatar--init" style={{ width: size, height: size, fontSize: size * 0.38 }} aria-label={name}>{initials(name)}</span>
  );
}

export default function AppLayout() {
  const { user } = useAuth();
  const { profile, settings } = useAppData();
  const { pathname } = useLocation();

  useEffect(() => { window.scrollTo({ top: 0 }); }, [pathname]);

  return (
    <div className={`app-shell ${settings.compactMode ? 'is-compact' : ''}`}>
      <header className="topbar">
        <Link to="/app" className="topbar__brand" aria-label="Food Verse AI dashboard">
          <LeafMark size={30} />
          <span>Food Verse AI</span>
        </Link>
        <GlobalSearch />
        <div className="topbar__right">
          <NotificationBell />
          <Link to="/app/profile" className="topbar__avatar" aria-label="Open profile">
            <Avatar name={user?.name} src={profile.avatar} size={40} />
          </Link>
        </div>
      </header>
      <main className="app-main" id="main">
        <ErrorBoundary key={pathname}>
          <Suspense fallback={<PageLoader label="Loading…" />}>
            <div className="page-enter"><Outlet /></div>
          </Suspense>
        </ErrorBoundary>
      </main>
      <BottomNav />
    </div>
  );
}
