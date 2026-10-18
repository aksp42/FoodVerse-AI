import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, CornerDownLeft } from 'lucide-react';
import { NAV_ITEMS } from './BottomNav';
import { FOODS, RECIPES } from '../data/mock';
import { FoodTile } from './FoodArt';

function buildIndex() {
  return [
    ...NAV_ITEMS.map((n) => ({ kind: 'Page', label: n.label, to: n.to, icon: n.icon })),
    ...FOODS.map((f) => ({ kind: 'Food', label: f.name, sub: `${f.calories} kcal · ${f.cuisine}`, to: `/app/food?sample=${f.id}`, emoji: f.emoji })),
    ...RECIPES.map((r) => ({ kind: 'Recipe', label: r.name, sub: `${r.time} mins · ${r.diet}`, to: `/app/cooking?recipe=${r.id}`, emoji: r.emoji })),
  ];
}

export default function GlobalSearch() {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const navigate = useNavigate();
  const wrapRef = useRef(null);
  const inputRef = useRef(null);
  const index = useMemo(buildIndex, []);

  const results = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return index.filter((i) => i.kind === 'Page').slice(0, 7);
    return index.filter((i) => `${i.label} ${i.sub || ''} ${i.kind}`.toLowerCase().includes(term)).slice(0, 8);
  }, [q, index]);

  useEffect(() => setActive(0), [q]);

  useEffect(() => {
    const onDoc = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); inputRef.current?.focus(); setOpen(true); }
    };
    document.addEventListener('mousedown', onDoc);
    window.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDoc); window.removeEventListener('keydown', onKey); };
  }, []);

  const go = (item) => {
    navigate(item.to);
    setOpen(false);
    setQ('');
    inputRef.current?.blur();
  };

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(a + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === 'Enter' && results[active]) { e.preventDefault(); go(results[active]); }
    else if (e.key === 'Escape') { setOpen(false); inputRef.current?.blur(); }
  };

  return (
    <div className="gsearch" ref={wrapRef}>
      <label className="gsearch__box">
        <Search size={18} />
        <input
          ref={inputRef} value={q} onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)} onKeyDown={onKeyDown}
          placeholder="Search foods, recipes, pages…" aria-label="Search" role="combobox" aria-expanded={open} aria-controls="gsearch-list"
        />
        {q && (
          <button type="button" className="gsearch__clear" onClick={() => { setQ(''); inputRef.current?.focus(); }} aria-label="Clear search">
            <X size={16} />
          </button>
        )}
      </label>
      {open && (
        <ul className="gsearch__list" id="gsearch-list" role="listbox">
          {results.length === 0 && <li className="gsearch__empty">No results for “{q}”. Try “paneer”, “salad” or “planner”.</li>}
          {results.map((r, i) => {
            const Icon = r.icon;
            return (
              <li key={`${r.kind}-${r.to}`} role="option" aria-selected={i === active}>
                <button type="button" className={`gsearch__item ${i === active ? 'is-active' : ''}`} onMouseEnter={() => setActive(i)} onClick={() => go(r)}>
                  {Icon ? <span className="gsearch__ico"><Icon size={18} /></span> : <FoodTile emoji={r.emoji} size={34} rounded={10} seed={i} />}
                  <span className="gsearch__txt"><strong>{r.label}</strong>{r.sub && <small>{r.sub}</small>}</span>
                  <em>{r.kind}</em>
                  {i === active && <CornerDownLeft size={14} className="gsearch__enter" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
