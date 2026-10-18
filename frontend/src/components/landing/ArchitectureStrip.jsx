import { Cpu, Terminal, Database, Smartphone, ShieldCheck, Check } from 'lucide-react';

const ARCH_LAYERS = [
  {
    icon: Smartphone,
    title: 'Frontend Client',
    tech: 'React 18 + Vite',
    role: 'Responsive Single Page Application with dynamic theme tokens, Lucide icons, and Recharts interactive telemetry visualization.',
    specs: ['Sub-second HMR', 'Strict WCAG Accessibility', 'Zero Heavy Decorator Bloat'],
  },
  {
    icon: Terminal,
    title: 'Application Server',
    tech: 'FastAPI (Python)',
    role: 'Asynchronous REST gateway handling file uploads, Pydantic v2 data models, automated error recovery, and robust CORS headers.',
    specs: ['Async Non-blocking IO', 'Multipart Upload Support', 'OpenAPI Schema Specs'],
  },
  {
    icon: Cpu,
    title: 'AI Processing Engine',
    tech: 'Google Gemini Multimodal',
    role: 'Primary intelligence tier with vision-capable models (cascading across gemini-3.5-flash-lite, 3.5-flash, 3.7-flash) and generative LLM.',
    specs: ['Auto-failover on 429 Quotas', 'Structured JSON Output', 'Vision & Audio Capable'],
  },
  {
    icon: Database,
    title: 'Persistence Layer',
    tech: 'Local SQLite Engine',
    role: 'Zero-configuration relational database maintaining your private audit trails, nutrition history, and customized meal plan schedules.',
    specs: ['foodverse.db Storage', 'Local-first Privacy', 'Fast Aggregations'],
  },
];

export default function ArchitectureStrip() {
  return (
    <section className="arch-section" id="architecture" aria-labelledby="arch-heading">
      <div className="arch-head">
        <span className="pill pill--blue">
          <ShieldCheck size={14} /> Production-Grade Architecture
        </span>
        <h2 id="arch-heading">Under the Hood: System Architecture</h2>
        <p>
          Engineered as a clean, decoupled full-stack platform following modern industry patterns.
        </p>
      </div>

      <div className="arch-grid">
        {ARCH_LAYERS.map(({ icon: Icon, title, tech, role, specs }) => (
          <div key={title} className="arch-card">
            <div className="arch-card__head">
              <span className="arch-card__icon">
                <Icon size={22} />
              </span>
              <div>
                <strong className="arch-card__title">{title}</strong>
                <span className="arch-card__tech">{tech}</span>
              </div>
            </div>
            <p className="arch-card__role">{role}</p>
            <ul className="arch-card__specs">
              {specs.map((item) => (
                <li key={item}>
                  <Check size={13} className="arch-card__check" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="arch-note">
        <small>
          <strong>Model Architecture Note:</strong> Google Gemini Vision serves as the authoritative primary food recognition engine. Optional local classifiers (e.g. MobileNetV2 benchmarks) remain isolated and never silently override multimodal LLM inferences.
        </small>
      </div>
    </section>
  );
}
