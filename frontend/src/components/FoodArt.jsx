/** Hand-built SVG food illustrations so the UI has rich imagery without external assets. */

export function HeroBowl({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 420 420" role="img" aria-label="Colorful healthy food bowl illustration">
      <defs>
        <radialGradient id="hb-bowl" cx="0.4" cy="0.3" r="0.9">
          <stop offset="0" stopColor="#fffdf7" />
          <stop offset="1" stopColor="#f0e2c0" />
        </radialGradient>
        <radialGradient id="hb-rice" cx="0.5" cy="0.4" r="0.7">
          <stop offset="0" stopColor="#ffe9a8" />
          <stop offset="1" stopColor="#e9b95a" />
        </radialGradient>
        <linearGradient id="hb-avo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#c6e48b" />
          <stop offset="1" stopColor="#6aa84f" />
        </linearGradient>
        <filter id="hb-sh" x="-20%" y="-20%" width="140%" height="150%">
          <feDropShadow dx="0" dy="14" stdDeviation="14" floodColor="#7a5a10" floodOpacity="0.22" />
        </filter>
      </defs>
      <ellipse cx="210" cy="372" rx="150" ry="20" fill="#b58a2a" opacity="0.16" />
      <g filter="url(#hb-sh)">
        <path d="M40 200c0 100 70 160 170 160s170-60 170-160z" fill="url(#hb-bowl)" />
        <ellipse cx="210" cy="200" rx="170" ry="56" fill="#fff5de" />
      </g>
      <ellipse cx="210" cy="198" rx="150" ry="46" fill="url(#hb-rice)" />
      {/* leafy greens */}
      <g>
        <path d="M70 190c10-40 50-50 74-34-8 24-34 44-74 34z" fill="#58a83a" />
        <path d="M80 186c18-14 36-20 52-26" stroke="#c9ec9d" strokeWidth="2.500" fill="none" strokeLinecap="round" />
        <path d="M250 150c24-30 64-28 84-6-18 20-52 30-84 6z" fill="#3f9a34" />
        <path d="M262 150c20-4 40-4 60-2" stroke="#c9ec9d" strokeWidth="2.500" fill="none" strokeLinecap="round" />
      </g>
      {/* avocado slices */}
      <g>
        <path d="M130 166c18-26 52-26 66-4 10 18-4 40-30 42-26 2-46-18-36-38z" fill="#3b6d1f" />
        <path d="M138 168c14-20 42-20 52-3 8 14-3 31-24 33-20 2-36-14-28-30z" fill="url(#hb-avo)" />
        <circle cx="168" cy="178" r="11" fill="#9a5a24" />
        <circle cx="165" cy="175" r="3.500" fill="#c58a4a" />
      </g>
      {/* chickpeas */}
      {[[210, 168], [226, 176], [244, 168], [258, 182], [236, 190], [214, 188], [270, 170], [200, 200], [250, 202], [282, 190]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="9" fill={i % 2 ? '#e8a93b' : '#f2bd5a'} />
      ))}
      {/* tomato halves */}
      <circle cx="106" cy="210" r="19" fill="#e5483a" />
      <circle cx="106" cy="210" r="11" fill="#f26b52" />
      <circle cx="310" cy="204" r="17" fill="#e5483a" />
      <circle cx="310" cy="204" r="9" fill="#f26b52" />
      {/* corn + purple cabbage */}
      {[[300, 230], [312, 240], [288, 240]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="6" fill="#ffd23f" />)}
      {[[120, 238], [134, 246], [148, 240], [108, 246]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="6" fill="#7a3f8f" />)}
      {/* sesame */}
      {[[190, 150], [215, 148], [236, 152], [176, 176], [270, 148]].map(([x, y], i) => (
        <ellipse key={i} cx={x} cy={y} rx="3" ry="1.800" fill="#fff6dd" transform={`rotate(${i * 30} ${x} ${y})`} />
      ))}
      {/* floating leaves + orange */}
      <path d="M356 60c30 4 46 26 38 54-26-6-42-26-38-54z" fill="#6bbf4a" />
      <path d="M44 84c28-10 52 2 60 28-26 6-48-4-60-28z" fill="#8fd14f" />
      <circle cx="68" cy="40" r="15" fill="#f59a1b" />
      <path d="M60 36c3-5 9-6 14-3" stroke="#ffd770" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  );
}

const TILE_COLORS = ['#fff1c9', '#e8f4da', '#fde3d0', '#ffe9b8', '#e0f0d0', '#fdeccd'];

/** Rounded emoji "photo" tile — consistent food imagery for cards and meal grids. */
export function FoodTile({ emoji = '🍽️', size = 56, seed = 0, rounded = 16, className = '' }) {
  const bg = TILE_COLORS[Math.abs(seed) % TILE_COLORS.length];
  return (
    <span
      className={`food-tile ${className}`}
      style={{ width: size, height: size, borderRadius: rounded, background: `radial-gradient(circle at 30% 25%, #fff 0%, ${bg} 70%)`, fontSize: size * 0.54 }}
      aria-hidden="true"
    >
      {emoji}
    </span>
  );
}

/** Big banner used when an uploaded image isn't available — e.g. kitchen scene. */
export function KitchenArt({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 300 200" role="img" aria-label="Restaurant kitchen illustration">
      <rect width="300" height="200" fill="#eef3ee" />
      <rect y="120" width="300" height="80" fill="#cfd8d1" />
      <rect x="0" y="0" width="300" height="120" fill="#f5f8f4" />
      {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={i * 50} y="0" width="2" height="120" fill="#e0e8e0" />)}
      <rect x="20" y="70" width="140" height="70" rx="6" fill="#aab6ae" />
      <rect x="26" y="76" width="128" height="10" rx="3" fill="#dfe6e0" />
      <rect x="180" y="40" width="90" height="100" rx="6" fill="#b9c4bc" />
      <rect x="190" y="52" width="70" height="46" rx="4" fill="#dfe8e2" />
      <circle cx="225" cy="75" r="14" fill="#c9d4cc" />
      {[0, 1, 2].map((i) => <circle key={i} cx={40 + i * 40} cy="106" r="10" fill="#8c9a90" />)}
      <rect x="60" y="14" width="3" height="40" fill="#9aa89e" />
      <rect x="60" y="14" width="46" height="4" rx="2" fill="#9aa89e" />
      {[0, 1, 2].map((i) => <rect key={i} x={68 + i * 14} y="18" width="8" height="26" rx="2" fill="#7f8e84" />)}
      <circle cx="248" cy="160" r="12" fill="#f59a1b" opacity="0.8" />
    </svg>
  );
}
