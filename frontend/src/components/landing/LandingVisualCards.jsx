import { useState } from 'react';
import { ScanSearch, Sparkles, ShieldCheck, CheckCircle2, AlertTriangle, ChefHat, Calendar, Flame, Activity, ArrowRight, Eye, Cpu, Database } from 'lucide-react';
import { HeroBowl } from '../FoodArt';

/**
 * Three Advanced 3D Visual Cards representing the core AI workflows:
 * 1. AI Food Intelligence (Image Input -> Gemini Vision -> Food Insights)
 * 2. Freshness & Kitchen Safety (Produce/Kitchen Input -> Vision Analysis -> Safety Guidance)
 * 3. Smart Cooking & Personalized Nutrition (Ingredients -> Gemini LLM -> Custom Recipe & Plan)
 */
export default function LandingVisualCards() {
  const [activeTab1, setActiveTab1] = useState('macros');
  const [freshScore, setFreshScore] = useState(94);
  const [selectedIngredients, setSelectedIngredients] = useState(['Paneer', 'Spinach', 'Garlic', 'Olive Oil']);

  return (
    <div className="visual-cards-grid" aria-label="Interactive AI Visual Capabilities">
      {/* Visual Card 1: AI Food Intelligence */}
      <article className="vcard vcard--vision" tabIndex={0} aria-labelledby="vcard1-title">
        <div className="vcard__glow" />
        <header className="vcard__head">
          <span className="vcard__tag vcard__tag--green">
            <ScanSearch size={14} /> Gemini Vision Multimodal
          </span>
          <span className="vcard__pill">Live Scan View</span>
        </header>

        <div className="vcard__body">
          <h3 id="vcard1-title" className="vcard__title">AI Food Intelligence &amp; Nutrition</h3>
          <p className="vcard__desc">
            Instantly recognizes meals from photos, estimating serving portions, calories, and complete macronutrient profiles with verified transparency.
          </p>

          {/* Interactive 3D Scanning Frame */}
          <div className="vcard__viewport">
            <div className="vcard-scanner">
              <div className="vcard-scanner__laser" />
              <div className="vcard-scanner__corners">
                <span className="corner corner--tl" />
                <span className="corner corner--tr" />
                <span className="corner corner--bl" />
                <span className="corner corner--br" />
              </div>

              <div className="vcard-scanner__visual">
                <HeroBowl className="vcard-scanner__dish" />
              </div>

              {/* Bounding box marker */}
              <div className="vcard-scanner__bbox">
                <div className="vcard-scanner__bbox-tag">
                  <Eye size={12} />
                  <span>Avocado Quinoa Bowl</span>
                </div>
              </div>

              {/* Floating Insight Telemetry Overlays */}
              <div className="vcard-floating-badge vcard-floating-badge--kpi">
                <Flame size={15} className="vcard__ico-flame" />
                <div>
                  <strong>410 kcal</strong>
                  <small>Est. 320g serving</small>
                </div>
              </div>

              <div className="vcard-floating-badge vcard-floating-badge--confidence">
                <Sparkles size={14} className="vcard__ico-sparkle" />
                <div>
                  <strong>Gemini 3.5 Flash</strong>
                  <small>Structured JSON</small>
                </div>
              </div>
            </div>

            {/* Macro Breakdown Strip */}
            <div className="vcard-macros">
              <div className="vcard-macro-pill">
                <span className="vcard-macro-dot vcard-macro-dot--cal" />
                <span>Protein</span>
                <strong>14.2g</strong>
              </div>
              <div className="vcard-macro-pill">
                <span className="vcard-macro-dot vcard-macro-dot--carb" />
                <span>Carbs</span>
                <strong>52.0g</strong>
              </div>
              <div className="vcard-macro-pill">
                <span className="vcard-macro-dot vcard-macro-dot--fat" />
                <span>Fat</span>
                <strong>16.4g</strong>
              </div>
              <div className="vcard-macro-pill">
                <span className="vcard-macro-dot vcard-macro-dot--fiber" />
                <span>Fiber</span>
                <strong>8.5g</strong>
              </div>
            </div>
          </div>

          {/* Pipeline flow */}
          <div className="vcard-flow" aria-hidden="true">
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">1</span>
              <span>Image Upload</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step vcard-flow__step--active">
              <span className="vcard-flow__circle">2</span>
              <span>Gemini Vision</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">3</span>
              <span>Nutrition Output</span>
            </div>
          </div>
        </div>
      </article>

      {/* Visual Card 2: Freshness & Kitchen Safety */}
      <article className="vcard vcard--safety" tabIndex={0} aria-labelledby="vcard2-title">
        <div className="vcard__glow" />
        <header className="vcard__head">
          <span className="vcard__tag vcard__tag--orange">
            <ShieldCheck size={14} /> Spoilage &amp; Safety Guard
          </span>
          <span className="vcard__pill vcard__pill--safe">Visual Audit</span>
        </header>

        <div className="vcard__body">
          <h3 id="vcard2-title" className="vcard__title">Produce Freshness &amp; Kitchen Safety</h3>
          <p className="vcard__desc">
            Evaluates produce peel firmness, discoloration, and mold risks while auditing commercial kitchens for sanitation compliance and food safety hazards.
          </p>

          {/* Freshness Inspection Simulation Viewport */}
          <div className="vcard__viewport vcard__viewport--safety">
            <div className="fresh-inspect">
              <div className="fresh-inspect__graphic" aria-hidden="true">
                <div className="fresh-item fresh-item--tomato">
                  <span className="fresh-item__emoji">🍅</span>
                  <div className="fresh-item__ring" />
                </div>
                <div className="fresh-item fresh-item--greens">
                  <span className="fresh-item__emoji">🥬</span>
                </div>
              </div>

              <div className="fresh-meter">
                <div className="fresh-meter__head">
                  <span>Visual Quality Index</span>
                  <strong className="fresh-meter__val">{freshScore}% Fresh</strong>
                </div>
                <div className="fresh-meter__track">
                  <div className="fresh-meter__bar" style={{ width: `${freshScore}%` }} />
                </div>
                <div className="fresh-meter__labels">
                  <small>Critical</small>
                  <small>Use Soon</small>
                  <small className="fresh-meter__label--peak">Peak Freshness</small>
                </div>
              </div>

              {/* Observed Attributes */}
              <ul className="fresh-attrs">
                <li className="fresh-attr fresh-attr--ok">
                  <CheckCircle2 size={14} />
                  <span>Surface skin intact with natural sheen</span>
                </li>
                <li className="fresh-attr fresh-attr--ok">
                  <CheckCircle2 size={14} />
                  <span>Zero fungal growth or softness detected</span>
                </li>
                <li className="fresh-attr fresh-attr--info">
                  <Activity size={14} />
                  <span>Recommended: Store at 10–12°C, consume in 5–7 days</span>
                </li>
              </ul>
            </div>

            <div className="vcard-disclaimer">
              <AlertTriangle size={13} />
              <span>Visual analysis only. Cannot detect microscopic bacteria or pathogens.</span>
            </div>
          </div>

          {/* Pipeline flow */}
          <div className="vcard-flow" aria-hidden="true">
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">1</span>
              <span>Photo / Frame</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step vcard-flow__step--active">
              <span className="vcard-flow__circle">2</span>
              <span>Vision Inspection</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">3</span>
              <span>Storage Advice</span>
            </div>
          </div>
        </div>
      </article>

      {/* Visual Card 3: Smart Cooking & Personalized Nutrition */}
      <article className="vcard vcard--cooking" tabIndex={0} aria-labelledby="vcard3-title">
        <div className="vcard__glow" />
        <header className="vcard__head">
          <span className="vcard__tag vcard__tag--blue">
            <ChefHat size={14} /> Generative Cooking LLM
          </span>
          <span className="vcard__pill">Pantry Match</span>
        </header>

        <div className="vcard__body">
          <h3 id="vcard3-title" className="vcard__title">Smart Cooking &amp; Meal Intelligence</h3>
          <p className="vcard__desc">
            Transforms leftovers and pantry supplies into tailored step-by-step gourmet recipes, paired with automated 7-day caloric and dietary planning.
          </p>

          {/* Interactive Pantry & Recipe Canvas */}
          <div className="vcard__viewport vcard__viewport--cook">
            <div className="cook-studio">
              <div className="cook-studio__chips-label">
                <small>Detected Available Ingredients:</small>
              </div>
              <div className="cook-studio__chips">
                {selectedIngredients.map((item) => (
                  <span key={item} className="cook-chip">
                    {item}
                  </span>
                ))}
                <span className="cook-chip cook-chip--add">+ 3 More</span>
              </div>

              {/* Recipe card preview */}
              <div className="cook-recipe-card">
                <div className="cook-recipe-card__top">
                  <div>
                    <strong>Spinach Garlic Paneer Sauté</strong>
                    <small>High Protein · Under 20 Mins</small>
                  </div>
                  <span className="cook-recipe-card__badge">98% Match</span>
                </div>
                <div className="cook-recipe-steps">
                  <div className="cook-step">
                    <span className="cook-step__num">1</span>
                    <p>Sauté minced garlic in olive oil until golden and aromatic.</p>
                  </div>
                  <div className="cook-step">
                    <span className="cook-step__num">2</span>
                    <p>Toss fresh spinach with paneer cubes and warm spices.</p>
                  </div>
                </div>
              </div>

              {/* Mini 7-Day Macro Calendar Pill */}
              <div className="cook-calendar-pill">
                <Calendar size={14} className="vcard__ico-cal" />
                <div className="cook-calendar-pill__text">
                  <strong>7-Day Personalized Meal Plan Synced</strong>
                  <small>Daily Target: 2,000 kcal · Vegetarian Goal</small>
                </div>
              </div>
            </div>
          </div>

          {/* Pipeline flow */}
          <div className="vcard-flow" aria-hidden="true">
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">1</span>
              <span>Pantry Inputs</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step vcard-flow__step--active">
              <span className="vcard-flow__circle">2</span>
              <span>Gemini LLM</span>
            </div>
            <ArrowRight size={14} className="vcard-flow__arrow" />
            <div className="vcard-flow__step">
              <span className="vcard-flow__circle">3</span>
              <span>Recipe &amp; Plan</span>
            </div>
          </div>
        </div>
      </article>
    </div>
  );
}
