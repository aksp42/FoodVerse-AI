import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ChefHat, Plus, X, Clock, Users, Heart, CheckCircle2, Circle,
  Search, Trash2, Flame, BookOpen, ShoppingBasket, Sparkles, Bot, Download, Camera
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import { EmptyState, AnalysisLoader } from '../components/Feedback';
import { FoodTile } from '../components/FoodArt';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { generateAIRecipe, detectIngredientsFromImage } from '../utils/analysis';
import { PANTRY_SUGGESTIONS, RECIPES } from '../data/mock';
import { generateRecipePDF } from '../utils/pdfGenerator';

const norm = (s) => s.trim().toLowerCase();
const cap  = (s) => s.trim().charAt(0).toUpperCase() + s.trim().slice(1).toLowerCase();

function matchRecipe(recipe, pantry) {
  const have  = new Set(pantry.map(norm));
  const items = recipe.ingredients.map((i) => ({ ...i, have: have.has(norm(i.n)) }));
  const owned = items.filter((i) => i.have).length;
  return { ...recipe, items, owned, total: items.length, pct: Math.round((owned / items.length) * 100) };
}

export default function Cooking() {
  const { pantry, setPantry, savedRecipes, toggleSavedRecipe, profile, addActivity } = useAppData();
  const toast = useToast();
  const [params, setParams] = useSearchParams();

  const [input, setInput]         = useState('');
  const [inputError, setInputError] = useState('');
  const [query, setQuery]         = useState('');
  const [filter, setFilter]       = useState('all'); // all | diet | saved
  const [openId, setOpenId]       = useState(null);
  const [stepsDone, setStepsDone] = useState({});

  // AI recipe generation state
  const [aiLoading, setAiLoading]   = useState(false);
  const [aiRecipe, setAiRecipe]     = useState(null);   // generated recipe object
  const [aiOpenId, setAiOpenId]     = useState(false);  // controls AI recipe modal
  const [visionLoading, setVisionLoading] = useState(false);
  const [detectedVisionItems, setDetectedVisionItems] = useState([]);

  useEffect(() => {
    const id = params.get('recipe');
    if (id && RECIPES.some((r) => r.id === id)) setOpenId(id);
    if (id) setParams({}, { replace: true });
  }, [params, setParams]);

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVisionLoading(true);
    try {
      const res = await detectIngredientsFromImage(file);
      if (res.detected_ingredients && res.detected_ingredients.length > 0) {
        const added = [];
        res.detected_ingredients.forEach((item) => {
          const c = cap(item);
          if (!pantry.some((p) => norm(p) === norm(c))) {
            added.push(c);
          }
        });
        if (added.length > 0) {
          setPantry((p) => [...p, ...added]);
          setDetectedVisionItems((prev) => [...prev, ...added]);
          toast.success(`Vision detected: ${added.join(', ')}`);
        } else {
          toast.info('All detected ingredients are already in your list.');
        }
      } else {
        toast.warning(res.observations || 'No food ingredients clearly recognized in this image.');
      }
    } catch (err) {
      toast.error(err?.message || 'Could not recognize ingredients from image.');
    } finally {
      setVisionLoading(false);
      e.target.value = '';
    }
  };

  const addIngredient = (raw) => {
    const name = cap(raw || '');
    if (!name) { setInputError('Type an ingredient to add'); return; }
    if (name.length > 24) { setInputError('Ingredient name is too long'); return; }
    if (pantry.some((p) => norm(p) === norm(name))) { setInputError(`${name} is already in your list`); return; }
    setPantry((p) => [...p, name]);
    setInput(''); setInputError('');
  };

  const removeIngredient = (name) => setPantry((p) => p.filter((x) => x !== name));

  const matches = useMemo(
    () => RECIPES.map((r) => matchRecipe(r, pantry)).sort((a, b) => b.pct - a.pct || a.time - b.time),
    [pantry],
  );

  const dietOk = (r) => {
    const d = profile.diet;
    if (d === 'Vegan') return r.diet === 'vegan';
    if (d === 'Vegetarian' || d === 'Jain') return r.diet !== 'non-veg';
    return true;
  };

  const visible = matches.filter((r) => {
    if (filter === 'diet'  && !dietOk(r)) return false;
    if (filter === 'saved' && !savedRecipes.includes(r.id)) return false;
    if (query && !`${r.name} ${r.ingredients.map((i) => i.n).join(' ')}`.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  const top = matches.find((r) => dietOk(r) && r.pct > 0) || matches[0];
  const open = openId ? matches.find((r) => r.id === openId) : null;
  const suggestions = PANTRY_SUGGESTIONS.filter((s) => !pantry.some((p) => norm(p) === norm(s))).slice(0, 8);

  const openRecipe = (id) => { setOpenId(id); setStepsDone({}); };

  const finishCooking = () => {
    const recipe = open || aiRecipe;
    if (!recipe) return;
    addActivity('cook', `Cooked ${recipe.name}`, { meals: 1, calories: recipe.calories });
    toast.success(`Enjoy your ${recipe.name}! Added to today's log.`);
    setOpenId(null);
    setAiOpenId(false);
  };

  const toggleSave = (r) => {
    const saved = savedRecipes.includes(r.id);
    toggleSavedRecipe(r.id);
    toast.info(saved ? `Removed ${r.name} from saved` : `Saved ${r.name}`);
  };

  const downloadRecipe = (r) => {
    if (!r) return;
    try {
      generateRecipePDF(r);
      toast.success(`${r.name} Recipe (PDF) downloaded`);
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to export recipe PDF');
    }
  };

  // ── AI Recipe Generation ────────────────────────────────────────────────────
  const handleGenerateAI = async () => {
    if (pantry.length === 0) { toast.warning('Add at least one ingredient first.'); return; }
    setAiLoading(true);
    setAiRecipe(null);
    try {
      const recipe = await generateAIRecipe(
        pantry,
        profile.diet || 'Vegetarian',
        2,
        'Indian',
        {
          visual_identified_ingredients: detectedVisionItems.length > 0 ? detectedVisionItems : null,
          skill_level: 'Beginner',
        }
      );
      setAiRecipe(recipe);
      setAiOpenId(true);
      setStepsDone({});
      addActivity('cook', `AI generated recipe: ${recipe.name}`);
      toast.success(`AI created "${recipe.name}" just for you!`);
    } catch (err) {
      toast.error(err?.message || 'AI recipe generation failed. Check if the backend is running.');
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="page">
      <PageHeader title="Smart Cooking Assistant" icon={ChefHat} subtitle="Add ingredients you have — get recipes or let AI create one just for you." />

      <div className="cook-grid">
        {/* ── Left: Pantry ─────────────────────────────────────────────────── */}
        <Card
          title="Available Ingredients"
          subtitle={`${pantry.length} item${pantry.length === 1 ? '' : 's'}`}
          action={pantry.length > 0 && <Button variant="ghost" size="sm" icon={Trash2} onClick={() => setPantry([])}>Clear all</Button>}
        >
          <form className="add-row" onSubmit={(e) => { e.preventDefault(); addIngredient(input); }}>
            <div className={`field ${inputError ? 'field--error' : ''}`}>
              <div className="field__control">
                <Plus size={18} className="field__icon" />
                <input
                  className="has-icon"
                  value={input}
                  onChange={(e) => { setInput(e.target.value); setInputError(''); }}
                  placeholder="Add an ingredient (e.g. spinach)"
                  aria-label="Add ingredient"
                  list="pantry-suggest"
                />
                <datalist id="pantry-suggest">{PANTRY_SUGGESTIONS.map((s) => <option key={s} value={s} />)}</datalist>
              </div>
            </div>
            <Button type="submit" variant="primary">Add</Button>
          </form>
          {inputError && <p className="field__error" role="alert">{inputError}</p>}

          {pantry.length === 0 ? (
            <EmptyState icon={ShoppingBasket} title="Your pantry is empty" message="Add a few ingredients to see recipe suggestions." />
          ) : (
            <ul className="chips chips--removable" aria-label="Your ingredients">
              {pantry.map((p) => (
                <li key={p}>
                  <span className="chip chip--static">
                    {p}
                    <button onClick={() => removeIngredient(p)} aria-label={`Remove ${p}`}><X size={14} /></button>
                  </span>
                </li>
              ))}
            </ul>
          )}

          {suggestions.length > 0 && (
            <div className="samples">
              <span>Quick add:</span>
              <div className="chips">
                {suggestions.map((s) => <button key={s} className="chip chip--add" onClick={() => addIngredient(s)}><Plus size={13} /> {s}</button>)}
              </div>
            </div>
          )}

          {/* ── AI Generate & Vision Buttons ─────────────────────────────── */}
          <div style={{ marginTop: '16px', borderTop: '1px solid var(--cream-200)', paddingTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ position: 'relative' }}>
              <input
                type="file"
                accept="image/*"
                id="pantry-photo-upload"
                style={{ display: 'none' }}
                onChange={handleImageUpload}
                disabled={visionLoading}
              />
              <label htmlFor="pantry-photo-upload" style={{ width: '100%' }}>
                <Button
                  type="button"
                  variant="outline"
                  icon={visionLoading ? undefined : Camera}
                  loading={visionLoading}
                  block
                  onClick={() => document.getElementById('pantry-photo-upload')?.click()}
                >
                  {visionLoading ? 'Detecting Ingredients…' : '📷 Scan Ingredients from Photo'}
                </Button>
              </label>
            </div>
            <Button
              icon={aiLoading ? undefined : Sparkles}
              onClick={handleGenerateAI}
              loading={aiLoading}
              disabled={pantry.length === 0}
              block
              variant="primary"
            >
              {aiLoading ? 'Generating AI Recipe…' : '✨ Generate AI Recipe'}
            </Button>
            <p className="disclaimer" style={{ marginTop: '4px', textAlign: 'center' }}>
              <Bot size={13} /> Powered by Gemini AI — creates a custom recipe from your ingredients
            </p>
          </div>
        </Card>

        {/* ── Right: Suggested Recipe ────────────────────────────────────── */}
        <Card title="Suggested Recipe" className="suggested">
          {top && pantry.length > 0 ? (
            <div className="recipe-hero">
              <FoodTile emoji={top.emoji} size={92} rounded={22} seed={3} />
              <div className="recipe-hero__body">
                <h2>{top.name}</h2>
                <ul className="meta">
                  <li><Clock size={15} /> {top.time} mins</li>
                  <li><Users size={15} /> {top.servings} servings</li>
                  <li><Flame size={15} /> {top.calories} kcal</li>
                </ul>
                <div className="match">
                  <div className="match__bar"><i style={{ width: `${top.pct}%` }} /></div>
                  <span>{top.owned}/{top.total} ingredients ready</span>
                </div>
                <Button iconRight={BookOpen} onClick={() => openRecipe(top.id)}>View Full Recipe</Button>
              </div>
            </div>
          ) : (
            <EmptyState icon={ChefHat} title="No suggestion yet" message="Add ingredients and we'll pick the best recipe for you." />
          )}
        </Card>
      </div>

      {/* ── All Recipes ──────────────────────────────────────────────────────── */}
      <Card
        title="All recipes"
        subtitle="Ranked by how many ingredients you already have"
        action={(
          <div className="segmented" role="tablist" aria-label="Recipe filter">
            {[['all', 'All'], ['diet', 'My diet'], ['saved', `Saved (${savedRecipes.length})`]].map(([k, l]) => (
              <button key={k} role="tab" aria-selected={filter === k} className={filter === k ? 'is-on' : ''} onClick={() => setFilter(k)}>{l}</button>
            ))}
          </div>
        )}
      >
        <label className="inline-search">
          <Search size={18} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search recipes or ingredients" aria-label="Search recipes" />
          {query && <button onClick={() => setQuery('')} aria-label="Clear search"><X size={16} /></button>}
        </label>
        {visible.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No recipes found"
            message={filter === 'saved' ? 'Tap the heart on a recipe to save it here.' : 'Try a different search or filter.'}
            action={<Button variant="outline" size="sm" onClick={() => { setQuery(''); setFilter('all'); }}>Reset filters</Button>}
          />
        ) : (
          <div className="recipe-grid">
            {visible.map((r, i) => (
              <article key={r.id} className="recipe-card">
                <button
                  className={`heart ${savedRecipes.includes(r.id) ? 'is-on' : ''}`}
                  onClick={() => toggleSave(r)}
                  aria-label={savedRecipes.includes(r.id) ? `Unsave ${r.name}` : `Save ${r.name}`}
                  aria-pressed={savedRecipes.includes(r.id)}
                >
                  <Heart size={18} />
                </button>
                <button className="recipe-card__main" onClick={() => openRecipe(r.id)}>
                  <FoodTile emoji={r.emoji} size={68} rounded={18} seed={i} />
                  <h3>{r.name}</h3>
                  <p className="muted small">{r.time} mins · {r.calories} kcal</p>
                  <div className="match match--sm">
                    <div className="match__bar"><i style={{ width: `${r.pct}%` }} /></div>
                    <span>{r.pct}% match</span>
                  </div>
                  <span className={`tag tag--${r.diet === 'non-veg' ? 'red' : 'green'}`}>{r.diet}</span>
                </button>
              </article>
            ))}
          </div>
        )}
      </Card>

      {/* ── Static Recipe Modal ───────────────────────────────────────────────── */}
      <Modal
        open={!!open}
        onClose={() => setOpenId(null)}
        title={open?.name || ''}
        size="lg"
        footer={open && (
          <>
            <Button variant="outline" icon={Download} onClick={() => downloadRecipe(open)}>
              Download PDF
            </Button>
            <Button variant="outline" icon={Heart} onClick={() => toggleSave(open)}>
              {savedRecipes.includes(open.id) ? 'Saved' : 'Save recipe'}
            </Button>
            <Button onClick={finishCooking} icon={CheckCircle2}>I cooked this</Button>
          </>
        )}
      >
        {open && (
          <div className="recipe-detail">
            <ul className="meta">
              <li><Clock size={15} /> {open.time} mins</li>
              <li><Users size={15} /> {open.servings} servings</li>
              <li><Flame size={15} /> {open.calories} kcal</li>
            </ul>
            <h4 className="subhead">Ingredients Needed</h4>
            <ul className="ingredients">
              {open.items.map((i) => (
                <li key={i.n} className={i.have ? 'have' : 'miss'}>
                  {i.have ? <CheckCircle2 size={18} /> : <Circle size={18} />}
                  <span>{i.n} <small>({i.q})</small></span>
                  {!i.have && (
                    <button className="link-btn" onClick={() => { addIngredient(i.n); toast.success(`${i.n} added to your pantry`); }}>
                      I have this
                    </button>
                  )}
                </li>
              ))}
            </ul>
            <h4 className="subhead">
              Cooking Steps <small>{Object.values(stepsDone).filter(Boolean).length}/{open.steps.length} done</small>
            </h4>
            <ol className="steps-list">
              {open.steps.map((s, idx) => (
                <li key={s} className={stepsDone[idx] ? 'is-done' : ''}>
                  <button onClick={() => setStepsDone((d) => ({ ...d, [idx]: !d[idx] }))} aria-pressed={!!stepsDone[idx]}>
                    <span className="step-num">{stepsDone[idx] ? <CheckCircle2 size={16} /> : idx + 1}</span>
                    <span>{s}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
        )}
      </Modal>

      {/* ── AI Recipe Modal ───────────────────────────────────────────────────── */}
      <Modal
        open={aiOpenId && !!aiRecipe}
        onClose={() => setAiOpenId(false)}
        title={aiRecipe ? `✨ ${aiRecipe.name}` : ''}
        size="lg"
        footer={aiRecipe && (
          <>
            <Button variant="outline" icon={Download} onClick={() => downloadRecipe(aiRecipe)}>
              Download PDF
            </Button>
            <Button onClick={finishCooking} icon={CheckCircle2}>I cooked this</Button>
          </>
        )}
      >
        {aiRecipe && (
          <div className="recipe-detail">
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
              <span className="tag" style={{ background: 'linear-gradient(135deg,#6b3fa0,#a855f7)', color: '#fff', borderRadius: '20px', padding: '4px 12px', fontSize: '0.75rem' }}>
                <Bot size={12} style={{ marginRight: '4px' }} /> AI Generated
              </span>
              <span className="tag tag--green">{aiRecipe.diet}</span>
            </div>
            {aiRecipe.description && <p className="muted" style={{ marginBottom: '12px' }}>{aiRecipe.description}</p>}
            <ul className="meta">
              <li><Clock size={15} /> {aiRecipe.time} mins</li>
              <li><Users size={15} /> {aiRecipe.servings} servings</li>
              <li><Flame size={15} /> {aiRecipe.calories} kcal/serving</li>
            </ul>
            {aiRecipe.prep_time_mins != null && aiRecipe.cook_time_mins != null && (
              <p className="small muted" style={{ marginTop: '4px', marginBottom: '10px' }}>
                Prep: {aiRecipe.prep_time_mins} mins • Active Cook: {aiRecipe.cook_time_mins} mins
              </p>
            )}

            <h4 className="subhead">Ingredients</h4>
            <ul className="ingredients">
              {(aiRecipe.ingredients || []).map((i, idx) => (
                <li key={idx} className="have">
                  <CheckCircle2 size={18} />
                  <span>{i.n} <small>({i.q})</small></span>
                </li>
              ))}
            </ul>
            <h4 className="subhead">
              Cooking Steps <small>{Object.values(stepsDone).filter(Boolean).length}/{(aiRecipe.steps || []).length} done</small>
            </h4>
            <ol className="steps-list">
              {(aiRecipe.steps || []).map((s, idx) => (
                <li key={idx} className={stepsDone[idx] ? 'is-done' : ''}>
                  <button onClick={() => setStepsDone((d) => ({ ...d, [idx]: !d[idx] }))} aria-pressed={!!stepsDone[idx]}>
                    <span className="step-num">{stepsDone[idx] ? <CheckCircle2 size={16} /> : idx + 1}</span>
                    <span>{s}</span>
                  </button>
                </li>
              ))}
            </ol>

            {/* Cooking Tips */}
            {Array.isArray(aiRecipe.cooking_tips) && aiRecipe.cooking_tips.length > 0 && (
              <div style={{ marginTop: '14px', background: 'var(--cream-100)', padding: '10px 14px', borderRadius: '10px', border: '1px solid var(--cream-300)' }}>
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>Chef Tips & Technique:</strong>
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: 'var(--text-soft)', lineHeight: 1.5 }}>
                  {aiRecipe.cooking_tips.map((t, idx) => (
                    <li key={idx}>{t}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Food Safety Reminders */}
            {Array.isArray(aiRecipe.food_safety_reminders) && aiRecipe.food_safety_reminders.length > 0 && (
              <div style={{ marginTop: '10px', background: '#fef2f2', padding: '10px 14px', borderRadius: '10px', border: '1px solid #fee2e2' }}>
                <strong style={{ fontSize: '0.82rem', color: '#991b1b', display: 'block', marginBottom: '4px' }}>Food Safety Reminders:</strong>
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: '#b91c1c', lineHeight: 1.5 }}>
                  {aiRecipe.food_safety_reminders.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {aiRecipe.nutrition_tip && (
              <div className="note-box" style={{ marginTop: '12px' }}>
                💡 {aiRecipe.nutrition_tip}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
