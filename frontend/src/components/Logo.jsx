import { Link } from 'react-router-dom';

export function LeafMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <defs>
        <linearGradient id="lm-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8fd14f" />
          <stop offset="1" stopColor="#2f8a3c" />
        </linearGradient>
        <linearGradient id="lm-o" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffd770" />
          <stop offset="1" stopColor="#f59a1b" />
        </linearGradient>
      </defs>
      <path d="M6 38C6 18 20 6 42 6c0 20-11 34-31 34-1.6 0-3.200-.2-5-.8z" fill="url(#lm-g)" />
      <path d="M6 38C18 26 26 19 36 12" stroke="#fffaf0" strokeWidth="2.600" fill="none" strokeLinecap="round" />
      <path d="M28 32c4-1 8-4 10-8-1 5-4 9-10 11z" fill="url(#lm-o)" />
    </svg>
  );
}

export default function Logo({ to = '/', size = 32, light = false }) {
  return (
    <Link to={to} className={`logo ${light ? 'logo--light' : ''}`} aria-label="Food Verse AI home">
      <LeafMark size={size} />
      <span className="logo__text">Food Verse AI</span>
    </Link>
  );
}
