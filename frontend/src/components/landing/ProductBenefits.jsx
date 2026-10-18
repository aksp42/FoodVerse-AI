import { Sparkles, Utensils, Shield, HeartPulse, Zap, Clock } from 'lucide-react';

const BENEFITS = [
  {
    icon: Sparkles,
    tone: 'orange',
    title: 'Instant Nutritional Clarity',
    text: 'Capture any Indian or continental meal to instantly estimate portion size, calories, protein, carbs, and fats without manual logging fatigue.',
    badge: 'Multimodal Vision',
  },
  {
    icon: Shield,
    tone: 'green',
    title: 'Proactive Waste Reduction',
    text: 'Examine fruits, vegetables, and pantry items before they spoil. Get reliable storage tips to extend shelf life and cut grocery waste.',
    badge: 'Freshness Guard',
  },
  {
    icon: Utensils,
    tone: 'blue',
    title: 'Objective Kitchen Hygiene',
    text: 'Inspect kitchen surfaces, prep stations, and storage areas against standardized cleanliness rubrics with itemized corrective guidance.',
    badge: 'Safety Inspection',
  },
  {
    icon: HeartPulse,
    tone: 'orange',
    title: 'Adaptive Meal Planning',
    text: 'Generate structured 7-day meal plans matching your dietary constraints (vegetarian, eggetarian, vegan) and caloric objectives effortlessly.',
    badge: '7-Day Planner',
  },
];

export default function ProductBenefits() {
  return (
    <section className="benefits-section" id="benefits" aria-labelledby="benefits-heading">
      <div className="benefits-head">
        <span className="pill pill--orange">
          <Zap size={14} /> Built For Daily Life
        </span>
        <h2 id="benefits-heading">Why Choose FoodVerse AI?</h2>
        <p>
          Purpose-built intelligence designed to replace guesswork with clarity across your kitchen, plate, and health goals.
        </p>
      </div>

      <div className="benefits-grid">
        {BENEFITS.map(({ icon: Icon, tone, title, text, badge }) => (
          <article key={title} className={`benefit-card benefit-card--${tone}`}>
            <div className="benefit-card__top">
              <span className="benefit-card__icon">
                <Icon size={24} />
              </span>
              <span className="benefit-card__badge">{badge}</span>
            </div>
            <h3 className="benefit-card__title">{title}</h3>
            <p className="benefit-card__text">{text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
