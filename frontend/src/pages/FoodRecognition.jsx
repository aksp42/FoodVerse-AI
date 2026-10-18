import { useState } from 'react';
import { ScanSearch, Sparkles, Salad, ChevronRight, Flame, Dumbbell, Wheat, Droplet, Info, Bot, CheckCircle2, Download, AlertTriangle, Layers, HeartPulse } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import ImageUploader from '../components/ImageUploader';
import { AnalysisLoader, ErrorState } from '../components/Feedback';
import useImageUpload from '../hooks/useImageUpload';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { analyzeFood } from '../utils/analysis';
import { generateFoodRecognitionPDF } from '../utils/pdfGenerator';

function formatLabel(raw = '') {
  const overrides = {
    cholebhature: 'Chole Bhature',
    dabeli:       'Dabeli',
    kathiroll:    'Kathi Roll',
    kofta:        'Kofta',
    naan:         'Naan',
    pakora:       'Pakora',
    panipuri:     'Pani Puri',
    pavbhaji:     'Pav Bhaji',
    vadapav:      'Vada Pav',
    biryani:      'Biryani',
    dal:          'Dal',
    dhokla:       'Dhokla',
    dosa:         'Dosa',
    jalebi:       'Jalebi',
    paneer:       'Paneer',
  };
  return overrides[raw.toLowerCase()] ?? raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function FoodRecognition() {
  const upload = useImageUpload();
  const { addActivity } = useAppData();
  const toast = useToast();

  const [status, setStatus]       = useState('idle');   // idle | loading | done | error
  const [result, setResult]       = useState(null);
  const [errorMsg, setErrorMsg]   = useState('');

  const analyze = async () => {
    if (!upload.file) { upload.setError('Choose a food photo first'); return; }
    setStatus('loading');
    setResult(null);
    setErrorMsg('');
    try {
      const data = await analyzeFood(upload.file);
      setResult(data);
      setStatus('done');
      if (data.is_food !== false) {
        const cals = data.nutrition ? data.nutrition.calories : 0;
        addActivity('food', `Identified: ${formatLabel(data.predicted_class)}`, { meals: 1, calories: cals });
        toast.success(`Identified: ${formatLabel(data.predicted_class)}`);
      } else {
        toast.warning('Non-food or ambiguous image detected');
      }
    } catch (err) {
      setErrorMsg(err?.message || 'Could not analyze that image.');
      setStatus('error');
    }
  };

  const reset = () => {
    upload.clear();
    setResult(null);
    setStatus('idle');
    setErrorMsg('');
  };

  const downloadReport = () => {
    if (!result) return;
    try {
      generateFoodRecognitionPDF(result, upload.file?.name || 'food_plate.jpg');
      toast.success('Food Nutrition Report (PDF) downloaded');
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to generate PDF nutrition report');
    }
  };

  const nutrition = result?.nutrition;

  return (
    <div className="page">
      <PageHeader
        title="Food Recognition & Nutrition Analysis"
        icon={ScanSearch}
        subtitle="Visual food intelligence powered exclusively by Gemini Multimodal Vision AI, with transparent nutrition estimation."
      />

      <div className="two-col">
        {/* Left column: upload & AI Model Indicator */}
        <Card title="Upload Food Photo">
          {/* AI Engine Status Card */}
          <div style={{
            marginBottom: '16px',
            padding: '10px 14px',
            borderRadius: '12px',
            background: 'var(--cream-100)',
            border: '1px solid var(--cream-300)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#e0f2fe',
              color: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Bot size={18} />
            </div>
            <div>
              <strong style={{ display: 'block', fontSize: '0.84rem', color: 'var(--text-main)' }}>
                Gemini Vision (Multimodal AI)
              </strong>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Primary dish identification, visual ingredient cues & nutritional analysis
              </span>
            </div>
          </div>

          <ImageUploader
            preview={upload.preview}
            error={upload.error}
            onSelect={(f) => { if (upload.select(f)) { setStatus('idle'); setResult(null); setErrorMsg(''); } }}
            onClear={reset}
            title="Upload Food Image"
            disabled={status === 'loading'}
          />
          <div className="row-actions" style={{ marginTop: '12px' }}>
            <Button
              icon={Sparkles}
              onClick={analyze}
              loading={status === 'loading'}
              disabled={!upload.preview}
              block
            >
              Analyze Food & Nutrition
            </Button>
          </div>

          <div className="model-note" style={{ marginTop: '14px' }}>
            <span className="model-note__dot" />
            <span>
              Powered exclusively by <strong>Google Gemini Vision</strong> for deep multimodal visual and culinary reasoning.
            </span>
          </div>
        </Card>

        {/* Right column: result */}
        <Card title="Analysis & Nutrition Profile" className="result-card">
          {status === 'loading' && (
            <AnalysisLoader
              title="Gemini Vision inspecting food…"
              steps={['Processing image upload', 'Extracting visual and culinary features', 'Estimating transparent nutrition metrics']}
            />
          )}

          {status === 'error' && (
            <ErrorState
              title="Recognition failed"
              message={errorMsg || 'Could not analyze that image. Please try a clearer food photo.'}
              onRetry={analyze}
            />
          )}

          {status === 'idle' && (
            <div className="state state--empty">
              <span className="state__icon"><Salad size={26} /></span>
              <h4>Nothing analyzed yet</h4>
              <p>Upload a food photo and click <strong>Analyze Food & Nutrition</strong>.</p>
            </div>
          )}

          {status === 'done' && result && (
            <div className="predict-result">
              {upload.preview && (
                <img
                  src={upload.preview}
                  alt="Uploaded food"
                  className="predict-result__img"
                />
              )}

              {/* Pipeline Telemetry Badges */}
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                <span className="tag" style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', fontSize: '0.74rem', padding: '3px 8px', borderRadius: '8px' }}>
                  Engine: {result.engine || 'Gemini Vision'}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {result.preprocessing_applied && (
                    <span style={{ fontSize: '0.72rem', background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', padding: '2px 8px', borderRadius: '8px' }}>
                      OpenCV {result.preprocessing_applied.processed_dimensions?.[0]}×{result.preprocessing_applied.processed_dimensions?.[1]}
                    </span>
                  )}
                  {result.certainty && (
                    <span className={`pill ${result.is_food === false ? 'pill--amber' : 'pill--green'}`} style={{ fontSize: '0.74rem' }}>
                      Certainty: {result.certainty}
                    </span>
                  )}
                </div>
              </div>

              {/* NON-FOOD / UNCERTAIN IMAGE BANNER */}
              {result.is_food === false ? (
                <div style={{ marginTop: '14px', padding: '16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b45309', fontWeight: 600, fontSize: '0.92rem', marginBottom: '6px' }}>
                    <AlertTriangle size={18} />
                    <span>Non-Food or Ambiguous Image Detected</span>
                  </div>
                  <p style={{ fontSize: '0.86rem', color: '#92400e', margin: '0 0 10px 0', lineHeight: 1.5 }}>
                    {result.description || 'The uploaded photograph does not appear to contain recognizable food items or prepared meals.'}
                  </p>
                  {Array.isArray(result.visual_observations) && result.visual_observations.length > 0 && (
                    <div>
                      <strong style={{ fontSize: '0.8rem', color: '#b45309' }}>Detected Elements:</strong>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px', fontSize: '0.8rem', color: '#78350f' }}>
                        {result.visual_observations.map((obs, i) => <li key={i}>{obs}</li>)}
                      </ul>
                    </div>
                  )}
                  <p style={{ fontSize: '0.78rem', color: '#b45309', margin: '12px 0 0 0', fontStyle: 'italic' }}>
                    Tip: FoodVerse AI works best with clear, well-lit photos of cooked dishes, plated meals, or raw ingredients.
                  </p>
                </div>
              ) : (
                <>
                  {/* Primary Prediction */}
                  <div className="predict-top1" style={{ marginTop: '10px' }}>
                    <div className="predict-top1__label">
                      <span className="muted" style={{ fontSize: '0.8rem' }}>Identified Food Item</span>
                      <h2 className="predict-top1__name">{formatLabel(result.predicted_class)}</h2>
                    </div>
                  </div>

                  {result.description && (
                    <p style={{ fontSize: '0.86rem', color: 'var(--text-main)', margin: '8px 0 12px 0', lineHeight: 1.45 }}>
                      {result.description}
                    </p>
                  )}

                  {/* Identified Food Items / Ingredients */}
                  {Array.isArray(result.food_items) && result.food_items.length > 0 && (
                    <div style={{ marginBottom: '12px' }}>
                      <strong style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Identified Ingredients / Components:</strong>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                        {result.food_items.map((item, i) => (
                          <span key={i} style={{ fontSize: '0.76rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '2px 8px', color: 'var(--text-main)' }}>
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Visual Observations */}
                  {Array.isArray(result.visual_observations) && result.visual_observations.length > 0 && (
                    <div style={{ marginBottom: '14px' }}>
                      <strong style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Visual Observations:</strong>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px', fontSize: '0.82rem', color: 'var(--text-main)' }}>
                        {result.visual_observations.map((obs, i) => (
                          <li key={i}>{obs}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Nutrition Profile & Health Scoring */}
                  {nutrition && (
                    <div style={{ background: 'var(--cream-100)', padding: '16px', borderRadius: '16px', border: '1px solid var(--cream-300)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                        <div>
                          <strong style={{ fontSize: '0.94rem', color: 'var(--text-main)' }}>Estimated Nutritional Profile</strong>
                          {nutrition.data_source && (
                            <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              Source: {nutrition.data_source}
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: '0.76rem', background: '#fff', padding: '3px 8px', borderRadius: '8px', border: '1px solid var(--line)', color: 'var(--text-main)', fontWeight: 500 }}>
                          {nutrition.serving || '1 serving'}
                        </span>
                      </div>

                      {nutrition.status === 'insufficient_data' ? (
                        <div style={{ background: '#fff', border: '1px solid #fed7aa', borderRadius: '10px', padding: '12px', marginTop: '10px' }}>
                          <strong style={{ fontSize: '0.84rem', color: '#c2410c' }}>Insufficient Reference Data</strong>
                          <p style={{ fontSize: '0.78rem', color: '#9a3412', margin: '4px 0 0 0' }}>
                            {nutrition.message || 'Nutritional values could not be determined with sufficient confidence.'}
                          </p>
                        </div>
                      ) : (
                        <>
                          {/* 5-Column Macronutrient Grid */}
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(64px, 1fr))', gap: '8px', textAlign: 'center', marginTop: '10px' }}>
                            <div style={{ background: '#fff', padding: '8px 4px', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                              <span style={{ fontSize: '0.72rem', color: '#e8890c', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                                <Flame size={12} /> Cals
                              </span>
                              <strong style={{ fontSize: '1rem', color: 'var(--text-main)' }}>{nutrition.calories ?? '—'}</strong>
                              <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)' }}>kcal</span>
                            </div>

                            <div style={{ background: '#fff', padding: '8px 4px', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                              <span style={{ fontSize: '0.72rem', color: '#2f8a3c', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                                <Dumbbell size={12} /> Protein
                              </span>
                              <strong style={{ fontSize: '1rem', color: 'var(--text-main)' }}>{nutrition.protein != null ? `${nutrition.protein}g` : '—'}</strong>
                              <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)' }}>macro</span>
                            </div>

                            <div style={{ background: '#fff', padding: '8px 4px', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                              <span style={{ fontSize: '0.72rem', color: '#f59a1b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                                <Wheat size={12} /> Carbs
                              </span>
                              <strong style={{ fontSize: '1rem', color: 'var(--text-main)' }}>{nutrition.carbs != null ? `${nutrition.carbs}g` : '—'}</strong>
                              <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)' }}>energy</span>
                            </div>

                            <div style={{ background: '#fff', padding: '8px 4px', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                              <span style={{ fontSize: '0.72rem', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                                <Droplet size={12} /> Fats
                              </span>
                              <strong style={{ fontSize: '1rem', color: 'var(--text-main)' }}>{nutrition.fat != null ? `${nutrition.fat}g` : '—'}</strong>
                              <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)' }}>lipids</span>
                            </div>

                            <div style={{ background: '#fff', padding: '8px 4px', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                              <span style={{ fontSize: '0.72rem', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
                                <Salad size={12} /> Fiber
                              </span>
                              <strong style={{ fontSize: '1rem', color: 'var(--text-main)' }}>{nutrition.fiber != null ? `${nutrition.fiber}g` : '—'}</strong>
                              <span style={{ fontSize: '0.65rem', display: 'block', color: 'var(--text-muted)' }}>fiber</span>
                            </div>
                          </div>

                          {/* Health Score Card */}
                          {nutrition.health_score != null && (
                            <div style={{
                              marginTop: '12px',
                              padding: '12px 14px',
                              borderRadius: '12px',
                              background: '#fff',
                              border: '1px solid var(--cream-300)',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '8px'
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <HeartPulse size={16} color={nutrition.health_score >= 80 ? '#16a34a' : nutrition.health_score >= 65 ? '#0284c7' : '#d97706'} />
                                  <strong style={{ fontSize: '0.86rem', color: 'var(--text-main)' }}>Nutritional Balance Score</strong>
                                </div>
                                <span className="pill" style={{
                                  background: nutrition.health_score >= 80 ? '#dcfce7' : nutrition.health_score >= 65 ? '#e0f2fe' : '#fef3c7',
                                  color: nutrition.health_score >= 80 ? '#166534' : nutrition.health_score >= 65 ? '#0369a1' : '#b45309',
                                  fontWeight: 700,
                                  fontSize: '0.78rem'
                                }}>
                                  {nutrition.health_score} / 100 • {nutrition.health_score_label}
                                </span>
                              </div>

                              {/* Visual Progress Bar */}
                              <div style={{ height: '6px', width: '100%', background: '#e2e8f0', borderRadius: '999px', overflow: 'hidden' }}>
                                <div style={{
                                  height: '100%',
                                  width: `${Math.min(100, Math.max(5, nutrition.health_score))}%`,
                                  background: nutrition.health_score >= 80 ? 'linear-gradient(90deg, #22c55e, #16a34a)' : nutrition.health_score >= 65 ? 'linear-gradient(90deg, #38bdf8, #0284c7)' : 'linear-gradient(90deg, #f59e0b, #d97706)',
                                  borderRadius: '999px',
                                  transition: 'width 0.4s ease'
                                }} />
                              </div>

                              {/* Score Breakdown factors */}
                              {Array.isArray(nutrition.health_score_breakdown) && nutrition.health_score_breakdown.length > 0 && (
                                <div style={{ marginTop: '4px' }}>
                                  <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.74rem', color: 'var(--text-soft)', lineHeight: 1.45 }}>
                                    {nutrition.health_score_breakdown.map((pt, i) => (
                                      <li key={i}>{pt}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                Heuristic evaluation of this single serving. Not a clinical diagnosis of total daily diet.
                              </span>
                            </div>
                          )}

                          {/* Practical Dietary Insights */}
                          {Array.isArray(nutrition.insights) && nutrition.insights.length > 0 && (
                            <div style={{ marginTop: '12px', padding: '10px 12px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                              <strong style={{ fontSize: '0.8rem', color: 'var(--text-main)', display: 'block', marginBottom: '6px' }}>
                                Practical Dietary Insights:
                              </strong>
                              <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: '#334155', lineHeight: 1.45 }}>
                                {nutrition.insights.map((ins, i) => (
                                  <li key={i}>{ins}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Uncertainty Note */}
                          {nutrition.uncertainty_note && (
                            <p style={{ margin: '10px 0 0 0', fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                              <Info size={13} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--green-600)' }} />
                              <span>{nutrition.uncertainty_note}</span>
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  )}

                  <p className="disclaimer" style={{ marginTop: '12px' }}>
                    * Nutrition values are transparent estimates based on typical recipe proportions. Visual analysis is not a clinical laboratory measurement.
                  </p>

                  <Button variant="outline" icon={Download} onClick={downloadReport} block style={{ marginTop: '14px' }}>
                    Download Nutrition Report (PDF)
                  </Button>
                </>
              )}

              <Button variant="ghost" icon={ChevronRight} onClick={reset} block style={{ marginTop: '8px' }}>
                Analyze another image
              </Button>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
