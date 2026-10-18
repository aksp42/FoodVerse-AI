import { useState } from 'react';
import { Apple, CheckCircle2, AlertTriangle, XCircle, Sparkles, Clock, Info, Trash2, History, Snowflake, Bot, Download } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import ImageUploader from '../components/ImageUploader';
import { AnalysisLoader, ErrorState, EmptyState } from '../components/Feedback';
import useImageUpload from '../hooks/useImageUpload';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { analyzeFreshness } from '../utils/analysis';
import { fileToThumb } from '../utils/helpers';
import { generateFreshnessPDF } from '../utils/pdfGenerator';

const STATUS_UI = {
  fresh:            { icon: CheckCircle2, cls: 'ok' },
  aging:            { icon: AlertTriangle, cls: 'warn' },     // legacy compat
  moderately_fresh: { icon: AlertTriangle, cls: 'warn' },
  spoiled:          { icon: XCircle,       cls: 'bad' },
  inconclusive:     { icon: Info,          cls: 'muted' },
};

const STORAGE_TIPS = {
  fresh: ['Store in the crisper drawer at 4 °C.', 'Keep away from ethylene-producing fruit like bananas.', 'Wash only right before consumption.'],
  aging: ['Cook or blend today to avoid waste.', 'Chop and freeze for soups or smoothies.', 'Trim away softened or bruised areas.'],
  moderately_fresh: ['Cook or consume soon — the item is past peak freshness.', 'Trim and discard any bruised or softened portions.', 'Chop and freeze for soups or smoothies to avoid waste.'],
  spoiled: ['Discard immediately — do not taste to test.', 'Sanitize the container and surrounding items.', 'Never consume food exhibiting visible mold.'],
  inconclusive: ['Image quality was insufficient for a reliable assessment.', 'Apply smell and texture checks manually.', 'When in doubt about food safety, discard.'],
};

export default function Freshness() {
  const upload = useImageUpload();
  const { addActivity } = useAppData();
  const toast = useToast();
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [history, setHistory] = useState([]);

  const analyze = async () => {
    if (!upload.file) { upload.setError('Choose a food image first'); return; }
    setStatus('loading');
    setErrorMsg('');
    try {
      const [r, thumb] = await Promise.all([
        analyzeFreshness(upload.file), 
        fileToThumb(upload.file, 96).catch(() => '')
      ]);
      setResult(r); 
      setStatus('done');
      setHistory((h) => [{ 
        id: Date.now(), 
        name: r.food_item || upload.file.name, 
        status: r.status, 
        label: r.label, 
        certainty: r.certainty || 'Standard', 
        img: thumb, 
        at: new Date() 
      }, ...h].slice(0, 8));
      
      addActivity('freshness', `Freshness analysis: ${r.food_item || 'Item'} (${r.label})`);
      if (r.status === 'spoiled') {
        toast.warning('Potential spoilage detected. Safest to discard.', 'Food Safety Alert');
      } else if (r.status === 'inconclusive') {
        toast.warning('Assessment inconclusive — check image quality or apply manual inspection.', 'Inconclusive');
      } else {
        toast.success(`Evaluated as ${r.label}`);
      }
    } catch (err) {
      setErrorMsg(err?.message || 'Freshness analysis failed.');
      setStatus('error');
    }
  };

  const reset = () => { upload.clear(); setResult(null); setStatus('idle'); setErrorMsg(''); };

  const downloadReport = () => {
    if (!result) return;
    try {
      generateFreshnessPDF(result, upload.file?.name || 'freshness_sample.jpg');
      toast.success('Freshness Assessment Report (PDF) downloaded');
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to generate PDF freshness report');
    }
  };



  return (
    <div className="page">
      <PageHeader 
        title="Food Freshness & Spoilage Detection" 
        icon={Apple} 
        subtitle="Visual produce and food safety assessment powered by Gemini 3.8 Flash Vision." 
      />
      <div className="two-col">
        <Card title="Upload Food / Produce Photo">
          <ImageUploader 
            preview={upload.preview} 
            error={upload.error} 
            onSelect={(f) => { if (upload.select(f)) { setStatus('idle'); setResult(null); setErrorMsg(''); } }} 
            onClear={reset} 
            title="Upload Food Image" 
            disabled={status === 'loading'} 
          />
          <div className="row-actions" style={{ marginTop: '12px' }}>
            <Button icon={Sparkles} onClick={analyze} loading={status === 'loading'} disabled={!upload.preview} block>
              Analyze Freshness
            </Button>
          </div>
          <div className="model-note" style={{ marginTop: '14px' }}>
            <span className="model-note__dot" />
            <span>
              Powered by <strong>Gemini 3.8 Flash Vision</strong> — evaluates discoloration, softening, bruising, fungal risk, and estimated shelf life.
            </span>
          </div>
        </Card>

        <Card title="Freshness & Spoilage Assessment">
          {status === 'loading' && (
            <AnalysisLoader 
              title="Inspecting produce condition…" 
              steps={['Analyzing coloration & browning', 'Detecting surface texture defects & mold', 'Synthesizing shelf life recommendation']} 
            />
          )}
          {status === 'error' && (
            <ErrorState 
              title="Analysis failed" 
              message={errorMsg || "Could not evaluate that image. Try a clearer photo under direct lighting."} 
              onRetry={analyze} 
            />
          )}
          {status === 'idle' && (
            <EmptyState 
              icon={Apple} 
              title="No food item analyzed yet" 
              message="Upload a photo of fruit, vegetables, or leftovers and click Analyze Freshness." 
            />
          )}
          {status === 'done' && result && (() => {
            // Resolve status safely — never fall back silently to 'fresh' styling
            const resolvedUi = STATUS_UI[result.status] ?? STATUS_UI.inconclusive ?? { icon: Info, cls: 'muted' };

            // Optimal Storage label — only assert temperature for genuinely fresh items
            const storageLabel =
              result.status === 'spoiled'          ? 'Discard safely' :
              result.status === 'moderately_fresh' ? 'Cook or freeze soon' :
              result.status === 'inconclusive'     ? 'Manual inspection needed' :
              result.status === 'fresh'            ? 'Refrigerate (~4 °C)' :
              result.status === 'aging'            ? 'Cook or freeze soon' :
                                                    'Check storage guidance';

            // Recommendations: prefer API field over local tips
            const recs =
              Array.isArray(result.safety_recommendations) && result.safety_recommendations.length > 0
                ? result.safety_recommendations
                : Array.isArray(result.recommendations) && result.recommendations.length > 0
                ? result.recommendations
                : STORAGE_TIPS[result.status] ?? STORAGE_TIPS.inconclusive;

            // Limitations: prefer API field, fall back to disclaimer
            const limitationText = result.limitations || result.disclaimer ||
              'Visual inspection cannot guarantee food safety or identify microbiological contaminants.';

            return (
              <div className="fresh-result">
                <div className="fresh-result__top">
                  {upload.preview && <img src={upload.preview} alt="Analyzed produce" className="food-result__img" />}
                  <div className={`status-badge status-badge--${resolvedUi.cls}`}>
                    <resolvedUi.icon size={22} />
                    <div>
                      <strong>{result.label}</strong>
                      <small>{result.food_item ? `Item: ${result.food_item}` : 'Visual Assessment'}</small>
                    </div>
                  </div>
                </div>

                {/* Engine + evidence level */}
                <div style={{ marginTop: '10px', marginBottom: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                  <span className="tag" style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', fontSize: '0.72rem', padding: '2px 8px', borderRadius: '6px' }}>
                    <Bot size={12} style={{ display: 'inline', marginRight: '4px' }} />
                    {result.engine || 'Gemini Vision'}
                  </span>
                  {result.evidence_level && (
                    <span className="pill pill--green" style={{ fontSize: '0.72rem' }}>
                      Evidence: {result.evidence_level.charAt(0).toUpperCase() + result.evidence_level.slice(1)}
                    </span>
                  )}
                  {!result.evidence_level && result.certainty && (
                    <span className="pill pill--green" style={{ fontSize: '0.72rem' }}>
                      Certainty: {result.certainty}
                    </span>
                  )}
                </div>

                {/* Observed cues (Activity 3.2 list) */}
                {Array.isArray(result.observed_cues) && result.observed_cues.length > 0 && (
                  <div style={{ background: 'var(--cream-100)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--cream-300)', marginBottom: '12px' }}>
                    <strong style={{ fontSize: '0.82rem', display: 'block', marginBottom: '4px' }}>Visual Observations:</strong>
                    <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                      {result.observed_cues.map((cue, i) => <li key={i}>{cue}</li>)}
                    </ul>
                  </div>
                )}

                {/* Legacy observations dict — only when observed_cues absent */}
                {(!Array.isArray(result.observed_cues) || result.observed_cues.length === 0) && result.observations && (
                  <div style={{ background: 'var(--cream-100)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--cream-300)', marginBottom: '12px' }}>
                    <strong style={{ fontSize: '0.82rem', display: 'block', marginBottom: '4px' }}>Visual Observations:</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.4 }}>
                      {result.observations.color   && <div>• Color: {result.observations.color}</div>}
                      {result.observations.texture && <div>• Texture: {result.observations.texture}</div>}
                      {result.observations.defects && <div>• Defects: {result.observations.defects}</div>}
                    </div>
                  </div>
                )}

                {/* Checklist */}
                {Array.isArray(result.checks) && result.checks.length > 0 && (
                  <ul className="checklist">
                    {result.checks.map((c, i) => (
                      <li key={i} className={c.ok ? 'is-ok' : 'is-warn'}>
                        {c.ok ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                        <span>{c.text}</span>
                      </li>
                    ))}
                  </ul>
                )}

                <div className="info-pair" style={{ marginTop: '12px' }}>
                  <div>
                    <Clock size={18} />
                    <span>Estimated Shelf Window</span>
                    <strong>{result.shelf || 'See recommendations'}</strong>
                  </div>
                  <div>
                    <Snowflake size={18} />
                    <span>Optimal Handling</span>
                    <strong>{storageLabel}</strong>
                  </div>
                </div>

                <h4 className="subhead" style={{ marginTop: '14px' }}>Recommended Handling Steps</h4>
                <ul className="bullets">
                  {recs.map((t, idx) => <li key={idx}>{t}</li>)}
                </ul>

                {/* Limitations — Activity 3.2 required disclosure */}
                <p className="note-box" style={{ marginTop: '12px' }}>
                  <Info size={16} /> {limitationText}
                </p>

                <Button variant="outline" icon={Download} onClick={downloadReport} block style={{ marginTop: '14px' }}>
                  Download Freshness Audit (PDF)
                </Button>
              </div>
            );
          })()}
        </Card>
      </div>

      {/* History Card from Current User Session */}
      <Card 
        title="Recent Freshness Evaluations" 
        subtitle="Analyses conducted during your active session" 
        action={history.length > 0 && <Button variant="ghost" size="sm" icon={Trash2} onClick={() => setHistory([])}>Clear</Button>}
      >
        {history.length === 0 ? (
          <EmptyState icon={History} title="No checks yet" message="Evaluated food items will appear here as you analyze them." />
        ) : (
          <ul className="history">
            {history.map((h) => {
              const u = STATUS_UI[h.status] || STATUS_UI.fresh;
              return (
                <li key={h.id}>
                  {h.img ? <img src={h.img} alt="" /> : <span className="history__ph"><Apple size={18} /></span>}
                  <div>
                    <strong>{h.name}</strong>
                    <small>{h.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                  </div>
                  <span className={`pill pill--${u.cls}`}>{h.label}</span>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
