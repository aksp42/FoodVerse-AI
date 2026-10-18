import { Link } from 'react-router-dom';
import { ArrowRight, ScanSearch, Apple, ShieldCheck, ChefHat, CalendarDays, Sparkles, HeartPulse, Menu, X, ArrowUpRight, Flame, CheckCircle, Shield } from 'lucide-react';
import { useState } from 'react';
import Logo from '../components/Logo';
import Button from '../components/Button';
import { HeroBowl } from '../components/FoodArt';
import { useAuth } from '../context/AuthContext';
import LandingVisualCards from '../components/landing/LandingVisualCards';
import WorkflowSection from '../components/landing/WorkflowSection';
import ProductBenefits from '../components/landing/ProductBenefits';
import ArchitectureStrip from '../components/landing/ArchitectureStrip';

const CORE_MODULES = [
  {
    to: '/app/food',
    icon: ScanSearch,
    title: 'Food Recognition & Nutrition',
    tag: 'Vision AI',
    text: 'Capture any plate or dish to identify the cuisine, estimate portion weights, and calculate detailed calories and macronutrients instantly.',
    tone: 'green',
  },
  {
    to: '/app/freshness',
    icon: Apple,
    title: 'Freshness & Spoilage Detection',
    tag: 'Quality Index',
    text: 'Inspect raw fruits and vegetables for surface discoloration, skin decay, or rot signs with qualified storage and consumption advice.',
    tone: 'orange',
  },
  {
    to: '/app/hygiene',
    icon: ShieldCheck,
    title: 'Restaurant & Kitchen Hygiene',
    tag: 'Audit Engine',
    text: 'Score commercial or home kitchen cleanliness based on visible sanitation criteria, hazard logs, and itemized corrective checklists.',
    tone: 'blue',
  },
  {
    to: '/app/cooking',
    icon: ChefHat,
    title: 'Smart Cooking Assistant',
    tag: 'Generative LLM',
    text: 'Turn spare pantry ingredients into delicious step-by-step gourmet recipes with customized cooking times, dietary tags, and smart substitutions.',
    tone: 'orange',
  },
  {
    to: '/app/meal-planner',
    icon: CalendarDays,
    title: 'Personalized 7-Day Meal Planner',
    tag: 'Macro Sync',
    text: 'Generate balanced weekly breakfast, lunch, and dinner plans customized strictly to your caloric target, dietary choice, and budget.',
    tone: 'green',
  },
  {
    to: '/app',
    icon: HeartPulse,
    title: 'Health Tracking & Analytics',
    tag: 'SQLite Relational',
    text: 'Track real-time nutritional history and visualize 7-day intake charts and macro distributions backed by local SQLite persistence.',
    tone: 'blue',
  },
];

export default function Landing() {
  const { isAuthed } = useAuth();
  const [menu, setMenu] = useState(false);
  const primaryTo = isAuthed ? '/app' : '/signup';

  return (
    <div className="landing">
      {/* Top Navigation */}
      <header className="landing__nav" role="banner">
        <div className="landing__nav-inner">
          <Logo />
          <nav className={`landing__links ${menu ? 'is-open' : ''}`} aria-label="Site Navigation">
            <a href="#showcase" onClick={() => setMenu(false)}>Visual AI</a>
            <a href="#workflow" onClick={() => setMenu(false)}>How It Works</a>
            <a href="#features" onClick={() => setMenu(false)}>AI Modules</a>
            <a href="#benefits" onClick={() => setMenu(false)}>Benefits</a>
            <a href="#architecture" onClick={() => setMenu(false)}>Architecture</a>
            {isAuthed ? (
              <Button to="/app" size="sm" iconRight={ArrowRight}>Open Dashboard</Button>
            ) : (
              <div className="landing__auth-actions">
                <Link to="/login" className="landing__login" onClick={() => setMenu(false)}>Log In</Link>
                <Button to="/signup" size="sm" onClick={() => setMenu(false)}>Sign Up Free</Button>
              </div>
            )}
          </nav>
          <button
            className="icon-btn landing__burger"
            onClick={() => setMenu((m) => !m)}
            aria-label={menu ? 'Close menu' : 'Open menu'}
            aria-expanded={menu}
          >
            {menu ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero" aria-labelledby="hero-heading">
        <div className="hero__copy">
          <span className="pill pill--orange hero__pill">
            <Sparkles size={14} /> Multimodal Food Intelligence Agent
          </span>
          <h1 id="hero-heading">
            Smarter Food.<br />
            <em>Intelligence for Every Bite.</em>
          </h1>
          <p className="hero__lead">
            Harness vision-capable Google Gemini AI to identify meals, evaluate produce freshness, audit kitchen hygiene, generate contextual recipes, and curate personalized 7-day nutrition plans.
          </p>
          <div className="hero__cta">
            <Button to={primaryTo} size="lg" iconRight={ArrowRight}>
              Get Started
            </Button>
            <a href="#features" className="btn btn--outline btn--lg">
              Explore AI Features
            </a>
            <a href="#workflow" className="btn btn--ghost btn--lg">
              See How It Works
            </a>
          </div>

          <ul className="hero__trust" aria-label="Key Capabilities">
            <li>
              <strong>6</strong>
              <span>AI Modules</span>
            </li>
            <li>
              <strong>100%</strong>
              <span>Gemini Vision</span>
            </li>
            <li>
              <strong>7-Day</strong>
              <span>Meal Planning</span>
            </li>
            <li>
              <strong>Local</strong>
              <span>SQLite Storage</span>
            </li>
          </ul>
        </div>

        {/* 3D Interactive Hero Showcase */}
        <div className="hero__art" aria-hidden="true">
          <div className="hero__glow-sphere" />
          <div className="hero__scan-ring" />
          <HeroBowl className="hero__bowl" />

          {/* Floating Insight Cards */}
          <div className="float-card float-card--a">
            <span className="float-card__emoji">🥑</span>
            <div>
              <strong>Avocado Quinoa Bowl</strong>
              <small>410 kcal · 14.2g Protein</small>
            </div>
          </div>

          <div className="float-card float-card--b">
            <span className="dot dot--ok" />
            <div>
              <strong>94% Freshness Index</strong>
              <small>Vine Tomatoes · 6 Days Left</small>
            </div>
          </div>

          <div className="float-card float-card--c">
            <span className="float-card__ico-sparkle"><Sparkles size={14} /></span>
            <div>
              <strong>Gemini 3.5 Flash Active</strong>
              <small>Structured JSON Output</small>
            </div>
          </div>
        </div>
      </section>

      {/* 3D Visual Cards Showcase Section */}
      <section className="section section--fluid" id="showcase" aria-labelledby="showcase-heading">
        <div className="section__head">
          <span className="pill pill--green">
            <Sparkles size={14} /> Interactive 3D Showcase
          </span>
          <h2 id="showcase-heading">Experience the AI in Action</h2>
          <p>Explore the visual workflows powering our recognition, freshness analysis, and recipe synthesis.</p>
        </div>
        <LandingVisualCards />
      </section>

      {/* 6-Stage End-to-End Workflow */}
      <WorkflowSection />

      {/* Core AI Modules Full-Width Grid */}
      <section className="section section--fluid" id="features" aria-labelledby="features-heading">
        <div className="section__head">
          <span className="pill pill--orange">
            <Shield size={14} /> Comprehensive Toolkit
          </span>
          <h2 id="features-heading">Six Dedicated AI Food Modules</h2>
          <p>Integrated intelligence designed to solve food identification, quality assessment, and daily planning.</p>
        </div>
        <div className="feature-grid">
          {CORE_MODULES.map(({ to, icon: Icon, title, tag, text, tone }) => (
            <Link key={title} to={to} className={`feature-card feature-card--${tone}`}>
              <div className="feature-card__top">
                <span className="feature-card__icon">
                  <Icon size={24} />
                </span>
                <span className="feature-card__badge">{tag}</span>
              </div>
              <h3 className="feature-card__title">{title}</h3>
              <p className="feature-card__text">{text}</p>
              <span className="feature-card__link">
                <span>Launch Tool</span>
                <ArrowUpRight size={15} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Product Benefits */}
      <ProductBenefits />

      {/* Technical Architecture */}
      <ArchitectureStrip />

      {/* Full-Width Premium CTA Banner */}
      <section className="cta-banner" id="cta" aria-labelledby="cta-heading">
        <div className="cta-banner__content">
          <span className="pill pill--orange cta-banner__pill">
            <Sparkles size={14} /> Transform Your Nutrition
          </span>
          <h2 id="cta-heading">
            Good Food Builds<br />
            a Healthier You <span aria-hidden="true">🧡</span>
          </h2>
          <p>
            Whether scanning dinner, auditing kitchen hygiene, or generating balanced 7-day recipes — FoodVerse AI is your reliable, multimodal intelligence companion.
          </p>
          <div className="cta-banner__actions">
            <Button to={primaryTo} variant="accent" size="lg" iconRight={ArrowRight}>
              Get Started
            </Button>
            <Button to="/app" variant="outline" size="lg">
              Explore Dashboard
            </Button>
          </div>
        </div>
        <div className="cta-banner__art" aria-hidden="true">
          <HeroBowl className="cta-banner__bowl" />
        </div>
      </section>

      {/* Full-Width Industry-Ready Footer */}
      <footer className="landing__foot" role="contentinfo">
        <div className="foot__top">
          <div className="foot__brand">
            <Logo size={32} />
            <p>
              FoodVerse AI provides multimodal intelligence for conscious eating, produce freshness preservation, kitchen hygiene audits, and automated nutrition planning.
            </p>
            <div className="foot__tech-tags">
              <span>Google Gemini AI</span>
              <span>FastAPI Backend</span>
              <span>React 18 + Vite</span>
              <span>SQLite Persistence</span>
            </div>
          </div>

          <div className="foot__columns">
            <div className="foot__col">
              <h4>AI Capabilities</h4>
              <Link to="/app/food">Food Recognition</Link>
              <Link to="/app/freshness">Freshness Detection</Link>
              <Link to="/app/hygiene">Hygiene Monitor</Link>
              <Link to="/app/cooking">Cooking Assistant</Link>
              <Link to="/app/meal-planner">Meal Planner</Link>
            </div>

            <div className="foot__col">
              <h4>Product Tour</h4>
              <a href="#showcase">3D Visual Cards</a>
              <a href="#workflow">6-Stage Pipeline</a>
              <a href="#features">Feature Grid</a>
              <a href="#benefits">User Benefits</a>
              <a href="#architecture">Architecture Specs</a>
            </div>

            <div className="foot__col">
              <h4>Application</h4>
              <Link to="/app">User Dashboard</Link>
              <Link to="/login">Account Login</Link>
              <Link to="/signup">Register Free</Link>
              <Link to="/app/profile">Profile Settings</Link>
            </div>

            <div className="foot__col">
              <h4>Author &amp; Project</h4>
              <p className="foot__author-note">
                Designed &amp; Developed by<br />
                <strong className="foot__author-name">Akanksha Singh</strong>
              </p>
              <small className="foot__author-title">
                Multimodal Food Intelligence System
              </small>
            </div>
          </div>
        </div>

        <div className="foot__divider" />

        <div className="foot__bottom">
          <div className="foot__disclaimer">
            <small>
              <strong>Disclaimer:</strong> FoodVerse AI estimates are designed for nutritional guidance and educational purposes only. They do not constitute certified medical diagnosis, laboratory testing, or certified food safety inspection.
            </small>
          </div>
          <div className="foot__meta">
            <p className="foot__credit">
              Designed &amp; Developed by <strong>Akanksha Singh</strong>
            </p>
            <small>© {new Date().getFullYear()} FoodVerse AI. All rights reserved.</small>
          </div>
        </div>
      </footer>
    </div>
  );
}
