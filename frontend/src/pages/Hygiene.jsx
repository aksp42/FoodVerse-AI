import { useMemo, useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, Sparkles, Download, ListChecks, TrendingUp, Info, Bot } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import ImageUploader from '../components/ImageUploader';
import ProgressRing from '../components/ProgressRing';
import { AnalysisLoader, ErrorState, EmptyState } from '../components/Feedback';
import { KitchenArt } from '../components/FoodArt';
import useImageUpload from '../hooks/useImageUpload';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { analyzeHygiene } from '../utils/analysis';
import { downloadTextFile } from '../utils/helpers';
import { generateHygieneAuditPDF } from '../utils/pdfGenerator';

const gradeColor = (s) => (s >= 85 ? 'var(--green-500)' : s >= 70 ? '#f0a020' : 'var(--red-500)');

export default function Hygiene() {
  const upload = useImageUpload({ kind: 'media', maxMB: 12 });
  const { addActivity } = useAppData();
  const toast = useToast();
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [scores, setScores] = useState([]);
  const [done, setDone] = useState({});

  const issues = useMemo(() => (result ? (result.findings || []).filter((f) => !f.ok) : []), [result]);

  const analyze = async () => {
    if (!upload.file) { upload.setError('Upload a kitchen image or video frame first'); return; }
    setStatus('loading'); 
    setDone({});
    setErrorMsg('');
    try {
      const r = await analyzeHygiene(upload.file);
      setResult(r); 
      setStatus('done');
      setScores((s) => [...s, { run: `#${s.length + 1}`, score: r.score }].slice(-8));
      addActivity('hygiene', `Hygiene analysis: ${r.score}/100 (${r.grade})`);
      toast.success(`Hygiene audit completed: ${r.score}/100 (${r.grade})`);
    } catch (err) {
      setErrorMsg(err?.message || 'Hygiene audit failed.');
      setStatus('error');
    }
  };

  const reset = () => { upload.clear(); setResult(null); setStatus('idle'); setDone({}); setErrorMsg(''); };

  const downloadReport = () => {
    if (!result) return;
    try {
      generateHygieneAuditPDF(result, upload.file?.name || 'kitchen-inspection.jpg');
      toast.success('Official Hygiene Audit Report (PDF) downloaded');
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to generate PDF audit report');
    }
  };

  return (
    <div className="page">
      <PageHeader 
        title="Restaurant Hygiene & Kitchen Safety Monitor" 
        icon={ShieldCheck} 
        subtitle="Visual sanitation inspection and safety scoring powered by Gemini 3.8 Flash Vision." 
      />
      <div className="two-col">
        <Card title="Kitchen / Restaurant Media">
          <ImageUploader
            accept="image/*,video/*" 
            preview={upload.preview} 
            isVideo={upload.isVideo} 
            error={upload.error}
            onSelect={(f) => { if (upload.select(f)) { setStatus('idle'); setResult(null); setErrorMsg(''); } }} 
            onClear={reset}
            title="Upload Kitchen Photo or Video" 
            buttonLabel="Select Media File" 
            buttonVariant="primary" 
            note="Supports JPG, PNG, WebP photos and MP4/WebM video clips" 
            disabled={status === 'loading'}
          />
          <div className="row-actions" style={{ marginTop: '12px' }}>
            <Button icon={Sparkles} onClick={analyze} loading={status === 'loading'} disabled={!upload.preview} block>
              Run Hygiene Audit
            </Button>
          </div>
          <div className="model-note" style={{ marginTop: '14px' }}>
            <span className="model-note__dot" />
            <span>
              Powered by <strong>Gemini 3.8 Flash Multimodal</strong> — evaluates surface sanitation, food storage coverage, pest control, and food safety compliance.
            </span>
          </div>
        </Card>

        <Card title="Hygiene Audit Report">
          {status === 'loading' && (
            <AnalysisLoader 
              title="Inspecting facility sanitation…" 
              steps={['Scanning food prep surfaces and countertops', 'Checking covered food storage & temperature safety', 'Auditing sanitation protocol adherence']} 
            />
          )}
          {status === 'error' && (
            <ErrorState 
              title="Audit failed" 
              message={errorMsg || "Could not process media file. Please upload a clear photo or video clip of the kitchen."} 
              onRetry={analyze} 
            />
          )}
          {status === 'idle' && (
            <div className="hygiene-idle">
              <KitchenArt className="hygiene-idle__art" />
              <EmptyState 
                icon={ShieldCheck} 
                title="No facility audited yet" 
                message="Upload a kitchen photo or video clip and tap Run Hygiene Audit." 
              />
            </div>
          )}
          {status === 'done' && result && (
            <div className="hyg-result">
              <div className="hyg-score">
                <ProgressRing 
                  value={result.score} 
                  size={128} 
                  stroke={13} 
                  color={gradeColor(result.score)} 
                  track="var(--cream-200)" 
                  label={`Hygiene score ${result.score} out of 100`}
                >
                  <div className="hyg-score__num">
                    <strong>{result.score}</strong>
                    <small>/100</small>
                  </div>
                </ProgressRing>
                <div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
                    <span className="tag" style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', fontSize: '0.72rem', padding: '2px 8px', borderRadius: '6px' }}>
                      <Bot size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      {result.engine || 'Gemini Vision'}
                    </span>
                    {result.media_type && (
                      <span className="pill pill--green" style={{ fontSize: '0.72rem' }}>
                        {result.media_type === 'video' ? '🎬 Video' : '📷 Image'}
                      </span>
                    )}
                    {result.coverage != null && (
                      <span className="pill pill--green" style={{ fontSize: '0.72rem' }}>
                        Coverage: {Math.round(result.coverage * 100)}%
                      </span>
                    )}
                  </div>
                  <h2 style={{ color: gradeColor(result.score), margin: 0 }}>{result.grade}</h2>
                  <p className="muted small" style={{ marginTop: '4px' }}>{result.summary || 'Inspection completed.'}</p>
                </div>
              </div>

              {/* Coverage / assessable indicators */}
              {result.assessable_indicators != null && (
                <div style={{ background: 'var(--cream-100)', padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--cream-300)', marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <strong>Evidence coverage:</strong> {result.assessable_indicators} of {result.total_indicators} indicators assessable
                  ({Math.round((result.coverage || 0) * 100)}% coverage).
                  Score calculated from assessable indicators only.
                </div>
              )}

              {/* Explicit Rubric Explanation */}
              {result.rubric_explanation && (
                <div style={{ background: 'var(--cream-100)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--cream-300)', marginTop: '12px' }}>
                  <strong style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Scoring Rubric:</strong>
                  <p style={{ margin: '3px 0 0 0', fontSize: '0.78rem', color: 'var(--text-main)' }}>{result.rubric_explanation}</p>
                </div>
              )}

              <h4 className="subhead" style={{ marginTop: '14px' }}>Sanitation Findings</h4>
              <ul className="checklist">
                {(result.findings || []).map((f, idx) => (
                  <li key={idx} className={f.ok ? 'is-ok' : 'is-warn'}>
                    {f.ok ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                    <span>{f.text}</span>
                  </li>
                ))}
              </ul>

              {/* Alerts with timestamps */}
              {Array.isArray(result.alerts) && result.alerts.length > 0 && (
                <>
                  <h4 className="subhead" style={{ marginTop: '14px', color: '#b3262b' }}>Hygiene Alerts</h4>
                  <ul className="checklist">
                    {result.alerts.map((a, idx) => (
                      <li key={idx} className="is-warn">
                        <AlertTriangle size={18} />
                        <span>
                          <strong>{a.label}</strong>
                          {a.timestamp_s != null && <> <small>[t={a.timestamp_s}s]</small></>}
                          {' — '}{a.evidence}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {/* Uncertain indicators */}
              {Array.isArray(result.uncertain_indicators) && result.uncertain_indicators.length > 0 && (
                <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', marginTop: '10px' }}>
                  <strong style={{ fontSize: '0.78rem', color: '#475569' }}>Uncertain (insufficient visual evidence):</strong>
                  <ul style={{ margin: '4px 0 0 0', paddingLeft: '16px', fontSize: '0.76rem', color: '#64748b' }}>
                    {result.uncertain_indicators.map((u, i) => (
                      <li key={i}>{u.label}: {u.reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              <Button variant="outline" icon={Download} onClick={downloadReport} block style={{ marginTop: '14px' }}>
                Download Official Report (PDF)
              </Button>
              <p className="disclaimer" style={{ marginTop: '10px' }}>
                <Info size={14} /> {result.limitations || result.disclaimer || 'Visual inspection is an advisory tool and not a certified regulatory inspection.'}
              </p>
            </div>
          )}
        </Card>
      </div>

      {status === 'done' && result && (
        <div className="two-col" style={{ marginTop: '16px' }}>
          <Card title="Corrective Actions" subtitle={issues.length ? 'Follow up on identified sanitation deficits' : undefined}>
            {issues.length === 0 ? (
              <EmptyState icon={ListChecks} title="Exemplary Standards" message="No critical violations identified in this image." />
            ) : (
              <ul className="todo">
                {(result.actionable_corrections || issues.map(i => i.text)).map((actionText, idx) => (
                  <li key={idx} className={done[idx] ? 'is-done' : ''}>
                    <label>
                      <input type="checkbox" checked={!!done[idx]} onChange={(e) => setDone((d) => ({ ...d, [idx]: e.target.checked }))} />
                      <span><strong>Action #{idx + 1}</strong><small>{actionText}</small></span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Session Audit History" subtitle="Scoring progression across analyses">
            {scores.length < 2 ? (
              <EmptyState icon={TrendingUp} title="Audit another station" message="Scan another kitchen area or frame to track score changes." />
            ) : (
              <div className="chart-box" style={{ height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={scores} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#efe6cf" />
                    <XAxis dataKey="run" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#4d6655' }} />
                    <YAxis domain={[40, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#86978b' }} />
                    <Tooltip formatter={(v) => [`${v}/100`, 'Score']} contentStyle={{ borderRadius: 12, border: '1px solid #efe6cf' }} />
                    <Line type="monotone" dataKey="score" stroke="#2f8a3c" strokeWidth={3} dot={{ r: 5, fill: '#f59a1b', strokeWidth: 0 }} activeDot={{ r: 7 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
