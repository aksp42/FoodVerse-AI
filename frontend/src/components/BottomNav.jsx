import { NavLink } from 'react-router-dom';
import { Home, ScanSearch, Apple, ShieldCheck, ChefHat, CalendarDays, User } from 'lucide-react';

export const NAV_ITEMS = [
  { to: '/app', label: 'Dashboard', icon: Home, end: true },
  { to: '/app/food', label: 'Food Recognition', icon: ScanSearch },
  { to: '/app/freshness', label: 'Freshness Detection', icon: Apple },
  { to: '/app/hygiene', label: 'Hygiene Monitor', icon: ShieldCheck },
  { to: '/app/cooking', label: 'Cooking Assistant', icon: ChefHat },
  { to: '/app/meal-planner', label: 'Meal Planner', icon: CalendarDays },
  { to: '/app/profile', label: 'Profile & Settings', icon: User },
];

/** Fixed, icon-only navigation. Labels live only in tooltips + aria-labels. */
export default function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Primary">
      <ul className="bottom-nav__list">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <li key={to}>
            <NavLink to={to} end={end} aria-label={label} className={({ isActive }) => `nav-item ${isActive ? 'nav-item--active' : ''}`}>
              <Icon size={22} strokeWidth={2.100} />
              <span className="nav-item__tip" role="tooltip">{label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
