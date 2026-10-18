import { Component } from 'react';
import { Loader2, AlertTriangle, RefreshCw, Inbox } from 'lucide-react';
import Button from './Button';
import { LeafMark } from './Logo';

export function Spinner({ size = 20, label }) {
  return (
    <span className="spinner" role="status">
      <Loader2 size={size} className="spin" />
      {label && <span>{label}</span>}
    </span>
  );
}

export function Skeleton({ h = 16, w = '100%', r = 8, className = '' }) {
  return <span className={`skeleton ${className}`} style={{ height: h, width: w, borderRadius: r }} aria-hidden="true" />;
}

export function PageLoader({ label = 'Loading Food Verse AI…' }) {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <div className="page-loader__mark"><LeafMark size={56} /></div>
      <p>{label}</p>
    </div>
  );
}

/** Card-sized loader used while an AI analysis is "running". */
export function AnalysisLoader({ title = 'Analyzing your image…', steps = [] }) {
  return (
    <div className="analysis-loader" role="status" aria-live="polite">
      <div className="analysis-loader__ring"><LeafMark size={34} /></div>
      <strong>{title}</strong>
      <ul>
        {steps.map((s, i) => (<li key={s} style={{ animationDelay: `${i * 0.5}s` }}>{s}</li>))}
      </ul>
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, message, action }) {
  return (
    <div className="state state--empty">
      <span className="state__icon"><Icon size={26} /></span>
      <h4>{title}</h4>
      {message && <p>{message}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ title = 'Something went wrong', message = 'Please try again in a moment.', onRetry, retryLabel = 'Try again' }) {
  return (
    <div className="state state--error" role="alert">
      <span className="state__icon"><AlertTriangle size={26} /></span>
      <h4>{title}</h4>
      <p>{message}</p>
      {onRetry && <Button variant="outline" size="sm" icon={RefreshCw} onClick={onRetry}>{retryLabel}</Button>}
    </div>
  );
}

export class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('UI error:', error, info); }
  reset = () => this.setState({ error: null });
  render() {
    if (this.state.error) {
      return (
        <div className="boundary">
          <ErrorState
            title="This page hit a snag"
            message="An unexpected error occurred. Your data is safe — reload this view to continue."
            onRetry={this.reset}
            retryLabel="Reload view"
          />
        </div>
      );
    }
    return this.props.children;
  }
}
