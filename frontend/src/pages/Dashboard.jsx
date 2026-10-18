import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ScanSearch, Apple, ShieldCheck, ChefHat, CalendarDays, Camera, Leaf, 
  ChevronRight, Lightbulb, Flame, Utensils, Target, Activity, RefreshCw, 
  CheckCircle2, ArrowUpRight, Sparkles, Database, Layers, ArrowRight
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, ReferenceLine, PieChart, Pie, Cell 
} from 'recharts';
import Card from '../components/Card';
import ProgressRing from '../components/ProgressRing';
import { EmptyState, Skeleton } from '../components/Feedback';
import { useAuth } from '../context/AuthContext';
import { useAppData } from '../context/AppDataContext';
import { greeting, timeAgo } from '../utils/helpers';

const FEATURES = [
  { to: '/app/food', icon: ScanSearch, title: 'Food Recognition', sub: 'Gemini Vision nutrition analysis', tone: 'green' },
  { to: '/app/freshness', icon: Apple, title: 'Freshness Detection', sub: 'Spoilage scan & safety audit', tone: 'green' },
  { to: '/app/hygiene', icon: ShieldCheck, title: 'Hygiene Monitor', sub: 'Sanitation scoring & safety', tone: 'blue' },
  { to: '/app/cooking', icon: ChefHat, title: 'Cooking Assistant', sub: 'Pantry recipes & instructions', tone: 'orange' },
  { to: '/app/meal-planner', icon: CalendarDays, title: 'Meal Planner', sub: 'Personalized caloric schedule', tone: 'orange' },
];

const ACT_ICON = { 
  food: Camera, 
  freshness: Leaf, 
  fresh: Leaf, 
  plan: CalendarDays, 
  hygiene: ShieldCheck, 
  cooking: ChefHat, 
  cook: ChefHat, 
  profile: Activity 
};

const TIPS = [
  'Eat the rainbow: three different colored vegetables per day cover most of your essential micronutrients.',
  'Store tomatoes at room temperature — refrigeration impairs their volatile flavor compounds.',
  'Drinking a glass of water 15 minutes before meals aids natural digestion and mindful satiety.',
  'Batch-cook lentils, dals, and whole grains at the start of the week to streamline healthy dinners.',
  'Pair iron-rich leafy greens with vitamin C (like lemon juice) to increase non-heme iron absorption by up to 3x.'
];

export default function Dashboard() {
  const { user } = useAuth();
  const { 
    stats, 
    calorieGoal, 
    progress, 
    activity, 
    profile, 
    weeklyCalories, 
    macroSplit, 
    todayMacros,
    hasTodayMeals,
    categoryDistribution,
    pantry,
    refreshFromBackend 
  } = useAppData();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [view, setView] = useState('calories'); // 'calories' | 'distribution'
  const tip = TIPS[new Date().getDate() % TIPS.length];

  useEffect(() => {
    refreshFromBackend();
    const t = setTimeout(() => setLoading(false), 250);
    return () => clearTimeout(t);
  }, [refreshFromBackend]);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await refreshFromBackend();
    setTimeout(() => setRefreshing(false), 450);
  };

  const firstName = user?.name?.split(' ')[0] || 'there';
  const weekly = (weeklyCalories || []).map((d) => ({ ...d, goal: calorieGoal }));
  const weeklyTotal = weekly.reduce((s, d) => s + (d.calories || 0), 0);
  const avg = Math.round(weeklyTotal / (weekly.length || 1));

  // Determine today's macro grams
  const proteinG = todayMacros?.protein || 0;
  const carbsG = todayMacros?.carbs || 0;
  const fatG = todayMacros?.fat || 0;
  const totalMacroG = proteinG + carbsG + fatG;

  // Real module counts for distribution view
  const categoryData = Array.isArray(categoryDistribution) && categoryDistribution.length > 0
    ? categoryDistribution
    : [
        { name: 'Food Recognition', module: 'food', count: stats?.meals || 0 },
        { name: 'Freshness Checks', module: 'freshness', count: 0 },
        { name: 'Hygiene Audits', module: 'hygiene', count: 0 },
        { name: 'AI Recipes', module: 'cooking', count: 0 },
        { name: 'Meal Plans', module: 'plan', count: 0 },
      ];

  return (
    <div className="page dash">
      {/* 1. Executive Welcome & Quick Action Banner */}
      <section className="dash__hero">
        <div className="dash__hero-main">
          <div className="dash__hero-badge">
            <span className="live-pulse" />
            <span className="badge-text">FoodVerse Intelligence Engine · Live Database</span>
          </div>
          <h1>{greeting()}, {firstName}! <span aria-hidden="true">👋</span></h1>
          <p>Your smart food companion for a healthier life</p>

          <div className="dash__hero-actions">
            <Link to="/app/food" className="hero-action-btn hero-action-btn--primary">
              <ScanSearch size={15} />
              <span>Scan Meal</span>
            </Link>
            <Link to="/app/freshness" className="hero-action-btn">
              <Apple size={15} />
              <span>Check Freshness</span>
            </Link>
            <Link to="/app/cooking" className="hero-action-btn">
              <ChefHat size={15} />
              <span>Smart Cook</span>
            </Link>
            <Link to="/app/meal-planner" className="hero-action-btn">
              <CalendarDays size={15} />
              <span>Plan Week</span>
            </Link>
          </div>
        </div>

        <div className="dash__hero-aside">
          <div className="sync-chip">
            <Database size={13} className="sync-chip__icon" />
            <span>SQLite Synced</span>
            <button 
              onClick={handleManualRefresh} 
              className={`sync-btn ${refreshing ? 'is-spinning' : ''}`}
              title="Refresh real metrics from database"
              aria-label="Refresh database metrics"
            >
              <RefreshCw size={13} />
            </button>
          </div>
          <div className="dash__hero-art" aria-hidden="true">🥗🍅🥑</div>
        </div>
      </section>

      {/* 2. Enterprise Tool Shortcuts Bar */}
      <section className="tool-grid" aria-label="FoodVerse AI Tools">
        {FEATURES.map(({ to, icon: Icon, title, sub, tone }) => (
          <Link key={to} to={to} className={`tool-card tool-card--${tone}`}>
            <div className="tool-card__header">
              <span className="tool-card__icon"><Icon size={20} /></span>
              <ChevronRight size={16} className="tool-card__go" />
            </div>
            <div className="tool-card__text">
              <strong>{title}</strong>
              <small>{sub}</small>
            </div>
          </Link>
        ))}
      </section>

      {/* 3. Primary KPI Overview (4 Balanced Cards) */}
      <section className="stat-row" aria-label="Key Performance Indicators">
        {loading ? (
          [0, 1, 2, 3].map((i) => (
            <div key={i} className="stat">
              <Skeleton h={16} w="55%" />
              <Skeleton h={32} w="70%" r={8} />
              <Skeleton h={12} w="85%" />
            </div>
          ))
        ) : (
          <>
            {/* KPI 1: Total Meals & Scans */}
            <div className="stat">
              <div className="stat__top">
                <span className="stat__label"><Utensils size={15} /> Total Meals Logged</span>
                <span className="stat__tag">Verified</span>
              </div>
              <strong className="stat__number">{stats.meals}</strong>
              <div className="stat__subtext">
                <span>{stats.totalScans || stats.meals} total AI analyses</span>
                <span className="stat__dot" />
                <span>SQLite</span>
              </div>
            </div>

            {/* KPI 2: Today's Calorie Intake */}
            <div className="stat">
              <div className="stat__top">
                <span className="stat__label"><Flame size={15} /> Today's Calories</span>
                <span className={`stat__tag ${stats.calories > calorieGoal ? 'stat__tag--warn' : 'stat__tag--success'}`}>
                  {stats.calories > calorieGoal ? 'Over Target' : 'On Track'}
                </span>
              </div>
              <strong className="stat__number">
                {stats.calories.toLocaleString()} <small>/ {calorieGoal.toLocaleString()} kcal</small>
              </strong>
              <div className="stat__progress-wrap">
                <div 
                  className="stat__progress-bar" 
                  style={{ width: `${Math.min(100, Math.round((stats.calories / calorieGoal) * 100))}%` }} 
                />
              </div>
              <div className="stat__subtext">
                {stats.calories > 0 
                  ? `${Math.max(0, calorieGoal - stats.calories).toLocaleString()} kcal remaining today` 
                  : 'No meals logged today yet'}
              </div>
            </div>

            {/* KPI 3: Today's Macronutrient Split */}
            <div className="stat">
              <div className="stat__top">
                <span className="stat__label"><Activity size={15} /> Today's Macros</span>
                <span className="stat__tag">Grams</span>
              </div>
              <div className="stat__macros-row">
                <div className="macro-chip macro-chip--pro">
                  <small>Protein</small>
                  <strong>{proteinG}g</strong>
                </div>
                <div className="macro-chip macro-chip--carb">
                  <small>Carbs</small>
                  <strong>{carbsG}g</strong>
                </div>
                <div className="macro-chip macro-chip--fat">
                  <small>Fat</small>
                  <strong>{fatG}g</strong>
                </div>
              </div>
              <div className="stat__subtext">
                {totalMacroG > 0 
                  ? `${totalMacroG}g total logged nutrition`
                  : 'Log today\'s meal to compute macros'}
              </div>
            </div>

            {/* KPI 4: Dietary Goal Progress */}
            <div className="stat stat--ring">
              <div className="stat__ring-copy">
                <span className="stat__label"><Target size={15} /> Goal Progress</span>
                <strong className="stat__goal">{profile.goal || 'Healthy Living'}</strong>
                <span className={`pill ${progress >= 100 ? 'pill--orange' : 'pill--green'}`}>
                  {progress >= 100 ? 'Goal Reached' : `${progress}% Tracked`}
                </span>
                <small className="stat__diet-tag">Diet: {profile.diet}</small>
              </div>
              <ProgressRing value={progress} size={78} stroke={8} />
            </div>
          </>
        )}
      </section>

      {/* 4. Analytics Grid: 7-Day Caloric Trends & Macronutrient Distribution */}
      <div className="dash__analytics-grid">
        {/* Left Column: Weekly Trends / Distribution Switcher */}
        <Card
          title="Intake & Analytics Trends"
          subtitle="7-day verified records from SQLite database"
          action={(
            <div className="segmented" role="tablist" aria-label="Chart view selector">
              <button 
                role="tab" 
                aria-selected={view === 'calories'} 
                className={view === 'calories' ? 'is-on' : ''} 
                onClick={() => setView('calories')}
              >
                7-Day Calories
              </button>
              <button 
                role="tab" 
                aria-selected={view === 'distribution'} 
                className={view === 'distribution' ? 'is-on' : ''} 
                onClick={() => setView('distribution')}
              >
                Module Activity
              </button>
            </div>
          )}
          className="dash__chart-card"
        >
          {loading ? (
            <Skeleton h={240} r={14} />
          ) : view === 'calories' ? (
            <div className="chart-wrapper">
              <div className="chart-box" style={{ height: 250, minHeight: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weekly} margin={{ top: 12, right: 12, left: -16, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(239, 230, 207, 0.75)" />
                    <XAxis 
                      dataKey="day" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#4d6655', fontSize: 12, fontWeight: 600 }} 
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#86978b', fontSize: 11 }} 
                    />
                    <Tooltip 
                      cursor={{ fill: 'rgba(107, 191, 74, 0.08)' }} 
                      contentStyle={{ 
                        borderRadius: 12, 
                        border: '1px solid #e2d9c4', 
                        boxShadow: '0 8px 24px rgba(15, 61, 34, 0.08)',
                        background: '#fff',
                        fontSize: '0.85rem'
                      }} 
                      formatter={(v) => [`${v} kcal`, 'Daily Intake']} 
                    />
                    <ReferenceLine 
                      y={calorieGoal} 
                      stroke="#f59a1b" 
                      strokeDasharray="4 4" 
                      strokeWidth={1.5}
                      label={{ 
                        value: `Target (${calorieGoal} kcal)`, 
                        fill: '#d97706', 
                        fontSize: 10, 
                        position: 'insideTopRight',
                        fontWeight: 600 
                      }} 
                    />
                    <Bar 
                      dataKey="calories" 
                      radius={[6, 6, 0, 0]} 
                      fill="#3d9130" 
                      animationDuration={600} 
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-footer-metrics">
                <div className="metric-pill">
                  <span className="metric-pill__label">7-Day Average</span>
                  <strong>{avg.toLocaleString()} kcal / day</strong>
                </div>
                <div className="metric-pill">
                  <span className="metric-pill__label">Weekly Total</span>
                  <strong>{weeklyTotal.toLocaleString()} kcal</strong>
                </div>
                <div className="metric-pill">
                  <span className="metric-pill__label">Daily Target</span>
                  <strong>{calorieGoal.toLocaleString()} kcal</strong>
                </div>
              </div>
            </div>
          ) : (
            <div className="chart-wrapper">
              <div className="category-bars-list">
                {categoryData.map((cat) => {
                  const maxCount = Math.max(1, ...categoryData.map(c => c.count));
                  const pct = Math.round((cat.count / maxCount) * 100);
                  return (
                    <div key={cat.name} className="cat-bar-item">
                      <div className="cat-bar-item__label">
                        <strong>{cat.name}</strong>
                        <span>{cat.count} {cat.count === 1 ? 'record' : 'records'}</span>
                      </div>
                      <div className="cat-bar-item__track">
                        <div 
                          className="cat-bar-item__fill" 
                          style={{ width: `${Math.max(6, pct)}%` }} 
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="chart-note">Activity distribution aggregated across SQLite audit records.</p>
            </div>
          )}
        </Card>

        {/* Right Column: Macronutrient Balance Donut */}
        <Card
          title="Macronutrient Balance"
          subtitle="Proportional split from recent meal analysis"
          className="dash__donut-card"
        >
          {loading ? (
            <Skeleton h={240} r={14} />
          ) : (
            <div className="donut-wrapper">
              <div className="donut-chart-box" style={{ height: 180, width: '100%', minHeight: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie 
                      data={macroSplit || []} 
                      dataKey="value" 
                      innerRadius={55} 
                      outerRadius={80} 
                      paddingAngle={4} 
                      animationDuration={600}
                    >
                      {(macroSplit || []).map((m) => (
                        <Cell key={m.name} fill={m.color} stroke="#fff" strokeWidth={2} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(v, n) => [`${v}%`, n]} 
                      contentStyle={{ 
                        borderRadius: 10, 
                        border: '1px solid #e2d9c4', 
                        boxShadow: '0 6px 18px rgba(15, 61, 34, 0.08)' 
                      }} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="donut-legend-grid">
                {(macroSplit || []).map((m) => (
                  <div key={m.name} className="donut-legend-item">
                    <div className="legend-item__indicator">
                      <span className="legend-item__dot" style={{ background: m.color }} />
                      <span className="legend-item__name">{m.name}</span>
                    </div>
                    <div className="legend-item__values">
                      <strong>{m.value}%</strong>
                      {m.grams > 0 && <small>{m.grams}g logged</small>}
                    </div>
                  </div>
                ))}
              </div>

              <div className="diet-alignment-box">
                <span className="diet-alignment-tag">Configured Diet: {profile.diet}</span>
                <p>Targets dynamically calibrated for your {profile.diet.toLowerCase()} lifestyle.</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* 5. Lower Section: Activity Stream & Contextual Intelligence */}
      <div className="dash__activity-grid">
        {/* Real Activity Stream from SQLite */}
        <Card 
          title="Recent Activity Log" 
          subtitle="Real-time audits, scans, and AI meal recommendations"
          className="dash__activity-card"
          action={
            <button 
              onClick={handleManualRefresh} 
              className={`icon-btn ${refreshing ? 'is-spinning' : ''}`}
              title="Refresh logs from database"
              aria-label="Refresh activity logs"
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
            >
              <RefreshCw size={15} />
            </button>
          }
        >
          {activity.length === 0 ? (
            <EmptyState 
              icon={Activity} 
              title="No activity recorded yet" 
              message="Run a food recognition scan, freshness check, or generate an AI recipe to view real SQLite activity records." 
            />
          ) : (
            <ul className="activity-stream">
              {activity.slice(0, 7).map((a) => {
                const Icon = ACT_ICON[a.type] || Activity;
                return (
                  <li key={a.id} className="activity-stream__item">
                    <span className={`activity__ico activity__ico--${a.type}`}>
                      <Icon size={16} />
                    </span>
                    <div className="activity-stream__content">
                      <p className="activity-stream__title">{a.text}</p>
                      <div className="activity-stream__meta">
                        <span className="activity-stream__type">{a.type}</span>
                        <span className="stat__dot" />
                        <span className="activity-stream__time">{a.ts ? timeAgo(a.ts) : 'Just now'}</span>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        {/* Intelligence Side Panel: Tip of the day + Pantry glance */}
        <div className="dash__insights-column">
          <Card className="tip-card enterprise-tip-card">
            <span className="tip-card__ico"><Lightbulb size={20} /></span>
            <div className="tip-card__body">
              <span className="tip-badge">Daily Food Intelligence</span>
              <strong>Smart Eating Tip</strong>
              <p>{tip}</p>
            </div>
          </Card>

          <Card 
            title="Pantry & Ingredients" 
            subtitle={`${pantry?.length || 0} tracked ingredients ready for AI recipes`}
            className="pantry-glance-card"
          >
            <div className="pantry-tags-wrap">
              {(pantry || []).slice(0, 8).map((item) => (
                <span key={item} className="pantry-pill">{item}</span>
              ))}
              {(pantry || []).length > 8 && (
                <span className="pantry-pill pantry-pill--more">+{pantry.length - 8} more</span>
              )}
            </div>
            <div className="pantry-action-footer">
              <Link to="/app/cooking" className="pantry-link">
                <span>Cook with pantry ingredients</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
