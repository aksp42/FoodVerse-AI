import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Wand2, Download, Trash2, Shuffle, Flame, CheckCircle2, Sparkles, Bot, Info, ShieldCheck, Check } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Cell } from 'recharts';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import { SelectField } from '../components/Fields';
import { EmptyState, AnalysisLoader } from '../components/Feedback';
import { FoodTile } from '../components/FoodArt';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { generateAIMealPlan, fetchSavedMealPlan } from '../utils/analysis';
import { DIETS, GOALS, BUDGETS, GOAL_CALORIES, MEAL_POOL, WEEK_DAYS } from '../data/mock';
import { downloadTextFile, mulberry32, shuffle } from '../utils/helpers';
import { generateMealPlanPDF } from '../utils/pdfGenerator';

const SLOTS = ['breakfast', 'lunch', 'dinner'];

// ── Fallback local plan generator (used when AI is unavailable) ───────────────
const COST_RANK = { Low: 0, Medium: 1, High: 2 };

function candidates(slot, { diet, budget, goal }) {
  let pool = MEAL_POOL[slot].filter((m) => m.diets.includes(diet) && COST_RANK[m.cost] <= COST_RANK[budget]);
  if (pool.length < 3) pool = MEAL_POOL[slot].filter((m) => m.diets.includes(diet));
  if (pool.length === 0) pool = MEAL_POOL[slot];
  const sorted = [...pool].sort((a, b) => a.cal - b.cal);
  if (sorted.length >= 4) {
    const half = Math.ceil(sorted.length / 2);
    if (goal === 'Weight Loss') return sorted.slice(0, half + 1);
    if (goal === 'Muscle Gain') return sorted.slice(-half - 1);
  }
  return sorted;
}

function generateLocalPlan(prefs) {
  const rand = mulberry32(Date.now() % 2147483647);
  const plan = { prefs, days: {}, ai_generated: false };
  const bag  = {};
  SLOTS.forEach((s) => { bag[s] = shuffle(candidates(s, prefs), rand); });
  WEEK_DAYS.forEach((d, di) => {
    plan.days[d] = {};
    SLOTS.forEach((s) => {
      const list = bag[s];
      plan.days[d][s] = list[di % list.length];
    });
  });
  return plan;
}

const dayTotal = (plan, d) => {
  if (!plan?.days?.[d]) return 0;
  if (plan.days[d].day_summary?.total_calories) return plan.days[d].day_summary.total_calories;
  return SLOTS.reduce((sum, s) => sum + (plan.days[d][s]?.cal || 0), 0);
};

const dayMacros = (plan, d) => {
  if (!plan?.days?.[d]) return { protein: 0, carbs: 0, fat: 0 };
  if (plan.days[d].day_summary) {
    return {
      protein: plan.days[d].day_summary.total_protein || 0,
      carbs: plan.days[d].day_summary.total_carbs || 0,
      fat: plan.days[d].day_summary.total_fat || 0,
    };
  }
  return SLOTS.reduce(
    (acc, s) => ({
      protein: acc.protein + (plan.days[d][s]?.protein || 0),
      carbs: acc.carbs + (plan.days[d][s]?.carbs || 0),
      fat: acc.fat + (plan.days[d][s]?.fat || 0),
    }),
    { protein: 0, carbs: 0, fat: 0 }
  );
};

export default function MealPlanner() {
  const { profile, updateProfile, mealPlan, setMealPlan, addActivity } = useAppData();
  const toast = useToast();

  const [diet, setDiet]       = useState(profile.diet   || 'Vegetarian');
  const [goal, setGoal]       = useState(profile.goal   || 'Weight Maintain');
  const [budget, setBudget]   = useState(profile.budget || 'Medium');
  const [planSpan, setPlanSpan] = useState('7');
  const [busy, setBusy]       = useState(false);
  const [useAI, setUseAI]     = useState(true);
  const [cell, setCell]       = useState(null);       // { day, slot }
  const [selectedDay, setSelectedDay] = useState('Mon');
  const [nutritionNote, setNutritionNote] = useState('');

  const goalCal = profile.calorie_target || GOAL_CALORIES[goal] || 1900;

  // ── Build plan (AI or local fallback) ────────────────────────────────────────
  const build = async ({ silent = false, forceLocal = false } = {}) => {
    setBusy(true);
    updateProfile({ diet, goal, budget });
    const daysCount = parseInt(planSpan, 10) || 7;

    if (useAI && !forceLocal) {
      try {
        const data = await generateAIMealPlan(
          diet,
          goal,
          budget,
          profile.allergies || '',
          daysCount,
          profile.user_id || 'default_user'
        );
        const plan = {
          ...data,
          prefs:           { diet, goal, budget, days: daysCount },
          target_calories: data.target_calories || goalCal,
          shopping_list:   data.shopping_list || null,
          ai_generated:    true,
          engine:          data.engine || 'Gemini 3.8 Flash LLM'
        };
        setMealPlan(plan);
        setNutritionNote(data.nutrition_notes || '');
        if (!silent) {
          addActivity('plan', `AI ${daysCount === 1 ? 'daily' : '7-day'} meal plan generated (${diet}, ${goal})`);
          toast.success(`✨ Your personalized AI ${daysCount === 1 ? 'daily' : '7-day'} meal plan is ready!`);
        }
        setBusy(false);
        return;
      } catch (err) {
        console.warn('AI meal plan error, falling back:', err.message);
        // Fall back gracefully to local planner if backend is offline/slow
        const plan = generateLocalPlan({ diet, goal, budget });
        plan.target_calories = goalCal;
        setMealPlan(plan);
        setNutritionNote('');
        setBusy(false);
        if (!silent) {
          toast.warning('Switched to local planner due to connection delay.');
        }
        return;
      }
    } else {
      const plan = generateLocalPlan({ diet, goal, budget });
      plan.target_calories = goalCal;
      setMealPlan(plan);
      setNutritionNote('');
      if (!silent) {
        addActivity('plan', `Local meal plan generated (${diet}, ${goal})`);
        toast.info('Generated meal plan using local optimization rules.');
      }
      setBusy(false);
    }
  };

  // Initial visit or refresh — fetch saved plan from SQLite or build silently
  useEffect(() => {
    let active = true;
    async function loadInitial() {
      if (!mealPlan) {
        try {
          const res = await fetchSavedMealPlan(profile.user_id || 'default_user');
          if (active && res?.plan?.days) {
            setMealPlan(res.plan);
            setNutritionNote(res.plan.nutrition_notes || '');
            return;
          }
        } catch {
          // ignore error and proceed
        }
        if (active) build({ silent: true });
      }
    }
    loadInitial();
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const displayedDays = useMemo(() => {
    if (!mealPlan?.days) return WEEK_DAYS;
    const keys = Object.keys(mealPlan.days);
    if (keys.length === 1 && keys[0] === 'Today') return ['Today'];
    return WEEK_DAYS.filter((d) => keys.includes(d)).length > 0
      ? WEEK_DAYS.filter((d) => keys.includes(d))
      : keys;
  }, [mealPlan]);

  const chartData = useMemo(() => (
    mealPlan && displayedDays.length > 1
      ? displayedDays.map((d) => ({ day: d, calories: dayTotal(mealPlan, d) }))
      : []
  ), [mealPlan, displayedDays]);

  const weeklyAvg = chartData.length
    ? Math.round(chartData.reduce((s, d) => s + d.calories, 0) / chartData.length)
    : (mealPlan && displayedDays.length === 1 ? dayTotal(mealPlan, displayedDays[0]) : 0);

  const swapMeal = (day, slot) => {
    const pool = candidates(slot, mealPlan.prefs || { diet, budget, goal }).filter((m) => m.name !== mealPlan.days[day][slot].name);
    if (pool.length === 0) { toast.info('No other options match your preferences.'); return; }
    const next = pool[Math.floor(Math.random() * pool.length)];
    setMealPlan({ ...mealPlan, days: { ...mealPlan.days, [day]: { ...mealPlan.days[day], [slot]: next } } });
    toast.success(`Swapped to ${next.name}`);
  };

  const selectAlternative = (day, slot, alt) => {
    if (!mealPlan?.days?.[day]?.[slot]) return;
    const currentMeal = mealPlan.days[day][slot];
    const updatedMeal = {
      ...currentMeal,
      name: alt.name,
      emoji: alt.emoji || currentMeal.emoji,
      cal: alt.cal,
      protein: alt.protein !== undefined ? alt.protein : currentMeal.protein,
      carbs: alt.carbs !== undefined ? alt.carbs : currentMeal.carbs,
      fat: alt.fat !== undefined ? alt.fat : currentMeal.fat,
      safety_adaptation_note: alt.reason ? `Adapted alternative: ${alt.reason}` : currentMeal.safety_adaptation_note,
    };
    setMealPlan({
      ...mealPlan,
      days: {
        ...mealPlan.days,
        [day]: {
          ...mealPlan.days[day],
          [slot]: updatedMeal,
        },
      },
    });
    toast.success(`Swapped to alternative: ${alt.name}`);
    setCell(null);
  };

  const clearPlan = () => { setMealPlan(null); setNutritionNote(''); toast.info('Meal plan cleared'); };

  const download = () => {
    if (!mealPlan) {
      toast.error('No meal plan available to download. Please generate a plan first.');
      return;
    }
    try {
      generateMealPlanPDF(mealPlan, {
        nutritionNote,
        goalCal,
        allergies: profile?.allergies || ''
      });
      toast.success('7-Day Meal Plan (PDF) downloaded');
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to generate PDF meal plan');
    }
  };

  const current = cell && mealPlan ? mealPlan.days[cell.day]?.[cell.slot] : null;

  return (
    <div className="page">
      <PageHeader
        title="Personalized Meal Planner"
        icon={CalendarDays}
        subtitle="Set your preferences — AI generates your perfect week of meals."
      />

      {/* ── Controls ────────────────────────────────────────────────────────── */}
      <Card className="planner-controls">
        <div className="controls-grid">
          <SelectField label="Dietary Preference" value={diet}   onChange={setDiet}   options={DIETS}   />
          <SelectField label="Daily Goal"          value={goal}   onChange={setGoal}   options={GOALS}   />
          <SelectField label="Budget"              value={budget} onChange={setBudget} options={BUDGETS} />
          <SelectField
            label="Duration"
            value={planSpan}
            onChange={setPlanSpan}
            options={[
              { value: '7', label: '7-Day Weekly Plan' },
              { value: '1', label: '1-Day Daily Plan' },
            ]}
          />
          <Button
            icon={useAI ? Sparkles : Wand2}
            onClick={() => build()}
            loading={busy}
            className="controls-grid__btn"
          >
            {mealPlan ? 'Regenerate Plan' : 'Generate Plan'}
          </Button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '10px', flexWrap: 'wrap' }}>
          <p className="muted small"><Flame size={14} /> Target for <strong>{goal}</strong>: about <strong>{goalCal.toLocaleString()} kcal/day</strong></p>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            <input
              type="checkbox"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              style={{ accentColor: 'var(--green-600)', width: '15px', height: '15px' }}
            />
            <Bot size={13} /> Use Gemini AI
          </label>
          {mealPlan?.ai_generated && (
            <span style={{ fontSize: '0.78rem', color: '#7c3aed', fontWeight: 600 }}>
              ✨ AI-powered plan active
            </span>
          )}
        </div>
      </Card>

      {busy && !mealPlan && (
        <Card>
          <AnalysisLoader
            title={useAI ? 'Gemini AI is building your plan…' : 'Building your plan…'}
            steps={['Analysing your preferences', 'Balancing calories across the week', 'Personalising meal variety']}
          />
        </Card>
      )}

      {!mealPlan && !busy && (
        <Card>
          <EmptyState
            icon={CalendarDays}
            title="No meal plan yet"
            message="Pick your preferences and generate a personalized plan."
            action={<Button icon={Sparkles} onClick={() => build()}>Generate my plan</Button>}
          />
        </Card>
      )}

      {mealPlan && (
        <>
          {/* Nutrition note from AI */}
          {nutritionNote && (
            <div className="note-box" style={{ marginBottom: '16px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <Info size={16} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--green-600)' }} />
              <span><strong>AI Nutrition Advice:</strong> {nutritionNote}</span>
            </div>
          )}

          {/* Adaptive recommendations from AI */}
          {mealPlan?.adaptive_recommendations && mealPlan.adaptive_recommendations.length > 0 && (
            <div className="note-box" style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--green-800)', fontWeight: 600 }}>
                <Sparkles size={16} />
                <span>Adaptive Goal Insights & Recommendations</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.86rem', color: 'var(--text-soft)', lineHeight: '1.5' }}>
                {mealPlan.adaptive_recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {mealPlan?.weekly_overview && (
            <p className="muted small" style={{ marginBottom: '12px', fontStyle: 'italic' }}>
              📋 {mealPlan.weekly_overview}
            </p>
          )}

          <Card
            title={`${planSpan === '1' ? 'Daily' : '7-Day'} Meal Plan`}
            subtitle={`${mealPlan.prefs?.diet || diet} · ${mealPlan.prefs?.goal || goal} · ${mealPlan.prefs?.budget || budget} budget${mealPlan.ai_generated ? ' · AI-generated' : ''} — tap a meal for details`}
            action={(
              <div className="btn-group">
                <Button variant="outline" size="sm" icon={Download} onClick={download}>Download PDF</Button>
                <Button variant="ghost"   size="sm" icon={Trash2}   onClick={clearPlan}>Clear</Button>
              </div>
            )}
            className={busy ? 'is-busy' : ''}
          >
            {/* Desktop table */}
            <div className="plan-scroll">
              <table className="plan-table">
                <thead>
                  <tr>
                    <th scope="col"><span className="sr-only">Meal</span></th>
                    {displayedDays.map((d) => <th key={d} scope="col">{d}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {SLOTS.map((s) => (
                    <tr key={s}>
                      <th scope="row" className="plan-slot">{s[0].toUpperCase() + s.slice(1)}</th>
                      {displayedDays.map((d, i) => {
                        const m = mealPlan.days[d]?.[s];
                        if (!m) return <td key={d}><span className="muted">—</span></td>;
                        return (
                          <td key={d}>
                            <button className="plan-cell" onClick={() => setCell({ day: d, slot: s })} aria-label={`${d} ${s}: ${m.name}, ${m.cal} kcal`}>
                              <FoodTile emoji={m.emoji} size={46} rounded={14} seed={i + s.length} />
                              <span>{m.name}</span>
                              {m.protein ? <small style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{m.protein}g P · {m.cal} kcal</small> : null}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                  <tr className="plan-total">
                    <th scope="row" className="plan-slot">Total</th>
                    {displayedDays.map((d) => {
                      const macros = dayMacros(mealPlan, d);
                      return (
                        <td key={d}>
                          <strong>{dayTotal(mealPlan, d)}</strong><small> kcal</small>
                          {macros.protein > 0 && (
                            <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                              P:{macros.protein}g C:{macros.carbs}g F:{macros.fat}g
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Mobile day view */}
            <div className="plan-mobile">
              <div className="day-tabs" role="tablist">
                {displayedDays.map((d) => (
                  <button key={d} role="tab" aria-selected={selectedDay === d} className={selectedDay === d ? 'is-on' : ''} onClick={() => setSelectedDay(d)}>{d}</button>
                ))}
              </div>
              <ul className="day-list">
                {SLOTS.map((s, i) => {
                  const m = mealPlan.days[selectedDay]?.[s];
                  if (!m) return null;
                  return (
                    <li key={s}>
                      <button onClick={() => setCell({ day: selectedDay, slot: s })}>
                        <FoodTile emoji={m.emoji} size={54} rounded={16} seed={i} />
                        <span><small>{s}</small><strong>{m.name}</strong></span>
                        <em>{m.cal} kcal</em>
                      </button>
                    </li>
                  );
                })}
                <li className="day-total">
                  Day total <strong>{dayTotal(mealPlan, selectedDay)} kcal</strong>
                  {(() => {
                    const macros = dayMacros(mealPlan, selectedDay);
                    return macros.protein > 0 ? (
                      <span className="muted small" style={{ display: 'block', marginTop: '2px' }}>
                        {macros.protein}g protein · {macros.carbs}g carbs · {macros.fat}g fat
                      </span>
                    ) : null;
                  })()}
                </li>
              </ul>
            </div>
          </Card>

          {/* Calorie chart */}
          {chartData.length > 1 && (
            <Card title="Daily calories vs target" subtitle={`Weekly average: ${weeklyAvg.toLocaleString()} kcal`}>
              <div className="chart-box" style={{ height: 230 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#efe6cf" />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#4d6655', fontSize: 12 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#86978b', fontSize: 12 }} domain={[0, (max) => Math.max(max, goalCal) + 200]} />
                    <Tooltip cursor={{ fill: 'rgba(107,191,74,0.1)' }} formatter={(v) => [`${v} kcal`, 'Planned']} contentStyle={{ borderRadius: 12, border: '1px solid #efe6cf' }} />
                    <ReferenceLine y={goalCal} stroke="#f59a1b" strokeDasharray="5 4" label={{ value: `Target ${goalCal}`, fill: '#e8890c', fontSize: 11, position: 'insideTopRight' }} />
                    <Bar dataKey="calories" radius={[8, 8, 0, 0]} animationDuration={600}>
                      {chartData.map((d) => <Cell key={d.day} fill={d.calories > goalCal ? '#fbb03b' : '#4aa83a'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="chart-note">Meals add up to your main intake; add a snack or fruit to reach your target.</p>
            </Card>
          )}

          {/* Medical disclaimer */}
          <p className="muted small" style={{ marginTop: '16px', textAlign: 'center', fontStyle: 'italic', fontSize: '0.78rem' }}>
            ℹ️ {mealPlan.medical_disclaimer || 'Calorie targets and meal plans are algorithmic estimates for educational and wellness guidance only. They do not constitute clinical nutritional prescriptions.'}
          </p>
        </>
      )}

      {/* ── Meal detail modal ─────────────────────────────────────────────────── */}
      <Modal
        open={!!current}
        onClose={() => setCell(null)}
        title={current ? `${cell.day} · ${cell.slot[0].toUpperCase() + cell.slot.slice(1)}` : ''}
        size="sm"
        footer={current && (
          <>
            <Button variant="outline" icon={Shuffle} onClick={() => swapMeal(cell.day, cell.slot)}>Swap meal</Button>
            <Button icon={CheckCircle2} onClick={() => {
              addActivity('food', `Logged ${current.name}`, { meals: 1, calories: current.cal });
              toast.success(`${current.name} logged`);
              setCell(null);
            }}>
              Log it
            </Button>
          </>
        )}
      >
        {current && (
          <div className="meal-modal">
            <FoodTile emoji={current.emoji} size={84} rounded={20} seed={current.cal} />
            <h2>{current.name}</h2>
            <p className="muted"><Flame size={15} /> {current.cal} kcal · {current.cost || 'Medium'} cost</p>

            {/* Macros row */}
            <div style={{ display: 'flex', gap: '6px', justifyContent: 'center', flexWrap: 'wrap', margin: '8px 0' }}>
              <span className="pill pill--green">Protein: {current.protein || 0}g</span>
              <span className="pill pill--orange">Carbs: {current.carbs || 0}g</span>
              <span className="pill" style={{ background: '#f3f4f6', color: '#374151' }}>Fat: {current.fat || 0}g</span>
              {current.prep_time_mins && (
                <span className="pill" style={{ background: '#f3f4f6', color: '#374151' }}>⏱️ {current.prep_time_mins} min prep</span>
              )}
            </div>

            {/* Diet tags */}
            <div className="chips">
              {(current.diets || []).slice(0, 4).map((d) => <span key={d} className="tag">{d}</span>)}
            </div>

            {/* Safety Adaptation Note */}
            {current.safety_adaptation_note && (
              <p className="muted small" style={{ background: '#ecfdf5', color: '#065f46', padding: '6px 10px', borderRadius: '8px', marginTop: '8px', textAlign: 'left' }}>
                🛡️ {current.safety_adaptation_note}
              </p>
            )}

            {/* Ingredients */}
            {current.ingredients && current.ingredients.length > 0 && (
              <div style={{ textAlign: 'left', marginTop: '12px', width: '100%' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-soft)', marginBottom: '4px' }}>Ingredients:</h4>
                <ul style={{ paddingLeft: '20px', fontSize: '0.82rem', margin: 0, color: 'var(--text-muted)' }}>
                  {current.ingredients.map((ing, i) => (
                    <li key={i}>{typeof ing === 'string' ? ing : `${ing.quantity || ''} ${ing.name || ''}`}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Practical instructions */}
            {current.instructions && (
              <div style={{ textAlign: 'left', marginTop: '10px', width: '100%' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-soft)', marginBottom: '4px' }}>Preparation:</h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0, lineHeight: '1.4' }}>{current.instructions}</p>
              </div>
            )}

            {/* Alternatives */}
            {current.alternatives && current.alternatives.length > 0 && (
              <div style={{ textAlign: 'left', marginTop: '14px', width: '100%' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-soft)', marginBottom: '6px' }}>Safe Alternatives:</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {current.alternatives.map((alt, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f9fafb', border: '1px solid var(--line)', borderRadius: '8px', padding: '8px 10px' }}>
                      <div style={{ flex: 1, paddingRight: '8px' }}>
                        <strong style={{ fontSize: '0.85rem' }}>{alt.name}</strong>
                        <p className="muted small" style={{ margin: 0 }}>{alt.cal} kcal · P: {alt.protein || 0}g · C: {alt.carbs || 0}g · F: {alt.fat || 0}g</p>
                        {alt.reason && <small style={{ color: 'var(--green-700)', display: 'block', fontSize: '0.75rem' }}>{alt.reason}</small>}
                      </div>
                      <Button size="sm" variant="outline" onClick={() => selectAlternative(cell.day, cell.slot, alt)}>
                        Use this
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
