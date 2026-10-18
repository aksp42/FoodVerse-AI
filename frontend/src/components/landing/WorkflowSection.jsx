import { useState } from 'react';
import { Camera, ShieldCheck, Cpu, FileText, Database, TrendingUp, Layers, CheckCircle2, ArrowRight } from 'lucide-react';

const WORKFLOW_STAGES = [
  {
    step: '01',
    id: 'user-input',
    icon: Camera,
    label: 'User Input',
    tag: 'Multimodal Intake',
    shortDesc: 'Upload a meal photo, produce picture, kitchen snapshot, or pantry ingredient list directly from any device.',
    details: 'Supports high-resolution camera captures, photo uploads, ingredient lists, and personal dietary preferences with zero manual typing friction.',
    highlights: ['Food photos & dishes', 'Produce & fruits', 'Kitchen & prep areas', 'Pantry ingredients'],
  },
  {
    step: '02',
    id: 'input-validation',
    icon: ShieldCheck,
    label: 'Input Validation',
    tag: 'Integrity Check',
    shortDesc: 'Verifies file format, resolution, and input safety before routing to the appropriate AI pipeline.',
    details: 'Enforces MIME-type validation (JPEG, PNG, WebP), payload size restrictions, and request integrity to protect processing speed and accuracy.',
    highlights: ['MIME format verification', 'Image dimension checks', 'Payload sanitization', 'Fast client/server guard'],
  },
  {
    step: '03',
    id: 'gemini-ai',
    icon: Cpu,
    label: 'Gemini Vision / Gemini LLM',
    tag: 'Core Intelligence',
    shortDesc: 'Vision-capable Gemini models analyze imagery while Gemini LLM synthesizes tailored recipes and meal schedules.',
    details: 'Visual food tasks leverage multimodal Gemini Vision with automatic failover, while culinary and planning reasoning runs through Gemini LLM.',
    highlights: ['Gemini Vision analysis', 'Generative recipe synthesis', 'Automated quota failover', 'Multimodal perception'],
  },
  {
    step: '04',
    id: 'insight-generation',
    icon: FileText,
    label: 'Insight Generation',
    tag: 'Structured Output',
    shortDesc: 'Transforms AI reasoning into clear, transparent nutrition metrics, freshness indexes, or structured recipe steps.',
    details: 'Outputs validated data: food identification, calorie & macro breakdowns with serving assumptions, produce storage advice, or step-by-step recipes.',
    highlights: ['Caloric & macro profiles', 'Freshness score & shelf life', 'Sanitation hazard logs', 'Step-by-step instructions'],
  },
  {
    step: '05',
    id: 'sqlite-persistence',
    icon: Database,
    label: 'SQLite Persistence',
    tag: 'Local Storage',
    shortDesc: 'Records analysis history, customized recipes, and 7-day meal plans locally for instant recall and total privacy.',
    details: 'Stores every successful audit, meal recognition, and generated plan in your private local SQLite database, powering your personal nutrition dashboard.',
    highlights: ['foodverse.db local database', 'Fast offline retrieval', 'Private historical logs', 'Meal plan synchronization'],
  },
  {
    step: '06',
    id: 'user-result',
    icon: TrendingUp,
    label: 'User Result',
    tag: 'Actionable Experience',
    shortDesc: 'Presents interactive nutrition charts, cooking guidance, hygiene checklists, and weekly goal progression.',
    details: 'Visualizes daily progress with interactive Recharts trends, interactive cooking checklists with ingredient toggles, and exportable weekly schedules.',
    highlights: ['Interactive macro charts', 'Cooking mode checklists', 'Hygiene corrective tasks', 'Goal progress rings'],
  },
];

export default function WorkflowSection() {
  const [selectedStage, setSelectedStage] = useState(0);
  const active = WORKFLOW_STAGES[selectedStage];

  return (
    <section className="workflow-section" id="workflow" aria-labelledby="workflow-heading">
      <div className="workflow-head">
        <span className="pill pill--green">
          <Layers size={14} /> AI Processing Workflow
        </span>
        <h2 id="workflow-heading">How FoodVerse AI Works</h2>
        <p>
          A transparent, end-to-end multimodal pipeline designed to transform everyday food images and dietary inputs into structured, reliable intelligence.
        </p>
      </div>

      {/* Horizontal Flow Pipeline (Desktop Track & Mobile Timeline) */}
      <div className="workflow-pipeline" role="tablist" aria-label="AI Processing Workflow Stages">
        <div className="workflow-track-line" aria-hidden="true">
          <div className="workflow-track-pulse" />
        </div>

        {WORKFLOW_STAGES.map(({ step, id, icon: Icon, label, tag, shortDesc }, index) => {
          const isSelected = selectedStage === index;
          return (
            <div
              key={id}
              role="tab"
              id={`wf-tab-${step}`}
              aria-controls={`wf-panel-${step}`}
              aria-selected={isSelected}
              tabIndex={0}
              className={`wf-node ${isSelected ? 'wf-node--active' : ''}`}
              onClick={() => setSelectedStage(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setSelectedStage(index);
                }
              }}
            >
              <div className="wf-node__marker">
                <span className="wf-node__step">{step}</span>
                <span className="wf-node__icon">
                  <Icon size={20} />
                </span>
              </div>

              <div className="wf-node__content">
                <span className="wf-node__tag">{tag}</span>
                <h3 className="wf-node__title">{label}</h3>
                <p className="wf-node__desc">{shortDesc}</p>
              </div>

              {index < WORKFLOW_STAGES.length - 1 && (
                <div className="wf-node__connector" aria-hidden="true">
                  <ArrowRight size={14} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Interactive Spotlight Card — Clean Product-Level Detail (No developer console) */}
      <div
        className="wf-spotlight"
        id={`wf-panel-${active.step}`}
        role="tabpanel"
        aria-labelledby={`wf-tab-${active.step}`}
      >
        <div className="wf-spotlight__banner">
          <div className="wf-spotlight__title-row">
            <span className="wf-spotlight__badge">
              Stage {active.step} of 06
            </span>
            <h4 className="wf-spotlight__heading">{active.label}</h4>
            <span className="wf-spotlight__tag">{active.tag}</span>
          </div>
          <p className="wf-spotlight__details">{active.details}</p>
        </div>

        <div className="wf-spotlight__highlights">
          <span className="wf-spotlight__highlights-label">Key Capabilities:</span>
          <ul className="wf-spotlight__chips">
            {active.highlights.map((item) => (
              <li key={item} className="wf-spotlight__chip">
                <CheckCircle2 size={13} />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
