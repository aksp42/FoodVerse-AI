import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, ArrowLeft, Sparkles, CheckCircle2 } from 'lucide-react';
import Logo from '../components/Logo';
import Button from '../components/Button';
import { TextField } from '../components/Fields';
import { HeroBowl } from '../components/FoodArt';
import { useAuth, DEMO_USER } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { validateEmail, validatePassword, validateName, passwordStrength } from '../utils/validators';

function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth__art">
        <Logo />
        <div className="auth__art-copy">
          <h2>Smarter Food.<br /><em>Healthier You.</em></h2>
          <p>Identify meals, check freshness, monitor kitchen hygiene and plan your week — all with AI.</p>
        </div>
        <HeroBowl className="auth__bowl" />
      </aside>
      <main className="auth__panel">
        <div className="auth__mobile-logo"><Logo /></div>
        <div className="auth__card">
          <Link to="/" className="auth__back" aria-label="Back to home">
            <ArrowLeft size={16} />
            <span>Back to home</span>
          </Link>
          <h1>{title}</h1>
          <p className="auth__sub">{subtitle}</p>
          {children}
        </div>
        <p className="auth__foot">{footer}</p>
      </main>
    </div>
  );
}

export function Login() {
  const { login, loginAsDemo } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/app';

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => {
    setForm((f) => ({ ...f, [k]: e.target.value }));
    if (errors[k]) setErrors((x) => ({ ...x, [k]: '' }));
    setFormError('');
  };

  const submit = async (e) => {
    e.preventDefault();
    const errs = {
      email: validateEmail(form.email),
      password: form.password ? '' : 'Password is required',
    };
    setErrors(errs);
    if (errs.email || errs.password) return;
    setBusy(true);
    try {
      const u = await login(form);
      toast.success(`Welcome back, ${u.name}!`);
      navigate(from, { replace: true });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const demo = async () => {
    setBusy(true);
    const u = await loginAsDemo();
    toast.success(`Signed in as ${u.name} (demo account)`);
    navigate(from, { replace: true });
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to continue your healthy journey."
      footer={<>New to Food Verse AI? <Link to="/signup">Create an account</Link></>}
    >
      <form onSubmit={submit} noValidate className="form">
        {formError && <div className="form-alert" role="alert">{formError}</div>}
        <TextField label="Email" type="email" icon={Mail} placeholder="you@example.com" value={form.email} onChange={set('email')} error={errors.email} autoComplete="email" />
        <TextField label="Password" type="password" icon={Lock} placeholder="Your password" value={form.password} onChange={set('password')} error={errors.password} autoComplete="current-password" />
        <Button type="submit" block size="lg" loading={busy} iconRight={ArrowRight}>Log in</Button>
      </form>
      <div className="divider"><span>or</span></div>
      <Button variant="outline" block icon={Sparkles} onClick={demo} disabled={busy}>Continue with demo account</Button>
      <p className="auth__hint">Demo: <code>{DEMO_USER.email}</code> / <code>{DEMO_USER.password}</code></p>
    </AuthShell>
  );
}

const STRENGTH = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'];

export function Signup() {
  const { signup } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', terms: false });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [k]: value }));
    if (errors[k]) setErrors((x) => ({ ...x, [k]: '' }));
    setFormError('');
  };

  const strength = passwordStrength(form.password);

  const submit = async (e) => {
    e.preventDefault();
    const errs = {
      name: validateName(form.name),
      email: validateEmail(form.email),
      password: validatePassword(form.password),
      confirm: form.confirm !== form.password ? 'Passwords do not match' : (form.confirm ? '' : 'Please confirm your password'),
      terms: form.terms ? '' : 'Please accept the terms to continue',
    };
    setErrors(errs);
    if (Object.values(errs).some(Boolean)) return;
    setBusy(true);
    try {
      const u = await signup(form);
      toast.success(`Account created. Welcome, ${u.name}!`);
      navigate('/app', { replace: true });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start eating smarter in under a minute."
      footer={<>Already have an account? <Link to="/login">Log in</Link></>}
    >
      <form onSubmit={submit} noValidate className="form">
        {formError && <div className="form-alert" role="alert">{formError}</div>}
        <TextField label="Full name" icon={User} placeholder="Akanksha Singh" value={form.name} onChange={set('name')} error={errors.name} autoComplete="name" />
        <TextField label="Email" type="email" icon={Mail} placeholder="you@example.com" value={form.email} onChange={set('email')} error={errors.email} autoComplete="email" />
        <div>
          <TextField label="Password" type="password" icon={Lock} placeholder="At least 8 characters" value={form.password} onChange={set('password')} error={errors.password} autoComplete="new-password" />
          {form.password && (
            <div className="strength" aria-live="polite">
              <div className={`strength__bar s${strength}`}><i /><i /><i /><i /></div>
              <span>{STRENGTH[strength]}</span>
            </div>
          )}
        </div>
        <TextField label="Confirm password" type="password" icon={Lock} placeholder="Re-enter password" value={form.confirm} onChange={set('confirm')} error={errors.confirm} autoComplete="new-password" />
        <div className={`check ${errors.terms ? 'check--error' : ''}`}>
          <label>
            <input type="checkbox" checked={form.terms} onChange={set('terms')} />
            <span>I agree to the Terms of Use and understand AI results are informational, not medical advice.</span>
          </label>
          {errors.terms && <p className="field__error" role="alert">{errors.terms}</p>}
        </div>
        <Button type="submit" block size="lg" loading={busy} iconRight={ArrowRight}>Create account</Button>
      </form>
      <ul className="perks">
        <li><CheckCircle2 size={16} /> Free to use</li>
        <li><CheckCircle2 size={16} /> Data stays in your browser</li>
      </ul>
    </AuthShell>
  );
}
