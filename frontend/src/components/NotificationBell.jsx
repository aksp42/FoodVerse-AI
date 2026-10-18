import { useEffect, useMemo, useRef, useState } from 'react';
import { Bell, Camera, Leaf, CalendarDays, CheckCheck, Trash2, BellOff } from 'lucide-react';
import { useAppData } from '../context/AppDataContext';
import { useAuth } from '../context/AuthContext';
import { loadJSON, saveJSON, timeAgo } from '../utils/helpers';

const ICONS = { food: Camera, fresh: Leaf, plan: CalendarDays, hygiene: Bell, cook: Bell, profile: Bell };

export default function NotificationBell() {
  const { activity, clearActivity } = useAppData();
  const { user } = useAuth();
  const seenKey = `fv_seen:${user?.email}`;
  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState(() => loadJSON(seenKey, 0));
  const ref = useRef(null);

  useEffect(() => {
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    window.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDoc); window.removeEventListener('keydown', onKey); };
  }, []);

  const unread = useMemo(() => activity.filter((a) => a.ts > seen).length, [activity, seen]);

  const markAllRead = () => {
    const now = Date.now();
    setSeen(now);
    saveJSON(seenKey, now);
  };

  return (
    <div className="notif" ref={ref}>
      <button className="icon-btn" onClick={() => setOpen((o) => !o)} aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`} aria-expanded={open}>
        <Bell size={20} />
        {unread > 0 && <span className="notif__badge">{unread > 9 ? '9+' : unread}</span>}
      </button>
      {open && (
        <div className="notif__panel" role="dialog" aria-label="Notifications">
          <header>
            <strong>Notifications</strong>
            <div>
              <button className="link-btn" onClick={markAllRead} disabled={unread === 0}><CheckCheck size={14} /> Mark read</button>
              <button className="link-btn" onClick={clearActivity} disabled={activity.length === 0}><Trash2 size={14} /> Clear</button>
            </div>
          </header>
          {activity.length === 0 ? (
            <div className="notif__empty"><BellOff size={26} /><p>You're all caught up.</p></div>
          ) : (
            <ul>
              {activity.slice(0, 8).map((a) => {
                const Icon = ICONS[a.type] || Bell;
                return (
                  <li key={a.id} className={a.ts > seen ? 'is-unread' : ''}>
                    <span className="notif__ico"><Icon size={16} /></span>
                    <div><p>{a.text}</p><small>{a.ts ? timeAgo(a.ts) : a.time}</small></div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
