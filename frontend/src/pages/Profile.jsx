import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, ShieldCheck, Salad, Target, Bell, LifeBuoy, Info, ChevronRight, Download, LogOut, Camera, Pencil, Mail, Phone, Lock, Send, ChevronDown, Trash2, Flame } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import ProgressRing from '../components/ProgressRing';
import { TextField, SelectField, Toggle } from '../components/Fields';
import { Avatar } from '../components/AppLayout';
import { LeafMark } from '../components/Logo';
import { useAuth } from '../context/AuthContext';
import { useAppData } from '../context/AppDataContext';
import { useToast } from '../context/ToastContext';
import { DIETS, GOALS, BUDGETS, GOAL_CALORIES, HELP_FAQ } from '../data/mock';
import { validateName, validatePhone, validatePassword, validateEmail } from '../utils/validators';
import { downloadTextFile, fileToThumb } from '../utils/helpers';
import { generateActivityReportPDF } from '../utils/pdfGenerator';
import { saveUserProfileAPI, fetchUserProfileAPI } from '../utils/analysis';

const ROWS = [
  { id: 'account', label: 'Account Settings', icon: User },
  { id: 'diet', label: 'Dietary Preferences', icon: Salad },
  { id: 'goals', label: 'Health Goals', icon: Target },
  { id: 'notifications', label: 'Notification Settings', icon: Bell },
  { id: 'help', label: 'Help & Support', icon: LifeBuoy },
  { id: 'about', label: 'About Food Verse AI', icon: Info },
];

export default function Profile() {
  const { user, updateSession, logout, changePassword } = useAuth();
  const { profile, updateProfile, settings, updateSettings, progress, stats, calorieGoal, activity } = useAppData();
  const toast = useToast();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [panel, setPanel] = useState(null);
  const [editing, setEditing] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);

  // Edit profile form
  const [form, setForm] = useState({
    name: user.name,
    phone: profile.phone || '',
    age: profile.age != null ? profile.age : '',
    height_cm: profile.height_cm != null ? profile.height_cm : '',
    weight_kg: profile.weight_kg != null ? profile.weight_kg : '',
  });
  const [errors, setErrors] = useState({});

  const openEdit = () => {
    setForm({
      name: user.name,
      phone: profile.phone || '',
      age: profile.age != null ? profile.age : '',
      height_cm: profile.height_cm != null ? profile.height_cm : '',
      weight_kg: profile.weight_kg != null ? profile.weight_kg : '',
    });
    setErrors({});
    setEditing(true);
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    const errs = { name: validateName(form.name), phone: validatePhone(form.phone) };
    if (form.age !== '' && form.age !== undefined && form.age !== null) {
      const a = Number(form.age);
      if (!Number.isInteger(a) || a < 1 || a > 120) {
        errs.age = 'Age must be between 1 and 120';
      }
    }
    if (form.height_cm !== '' && form.height_cm !== undefined && form.height_cm !== null) {
      const h = Number(form.height_cm);
      if (isNaN(h) || h < 50 || h > 250) {
        errs.height_cm = 'Height must be between 50 and 250 cm';
      }
    }
    if (form.weight_kg !== '' && form.weight_kg !== undefined && form.weight_kg !== null) {
      const w = Number(form.weight_kg);
      if (isNaN(w) || w < 20 || w > 300) {
        errs.weight_kg = 'Weight must be between 20 and 300 kg';
      }
    }

    setErrors(errs);
    if (Object.values(errs).some(Boolean)) return;

    const trimmedName = form.name.trim();
    const phoneVal = form.phone ? form.phone.trim() : '';
    const ageVal = form.age !== '' && form.age !== null ? parseInt(form.age, 10) : null;
    const heightVal = form.height_cm !== '' && form.height_cm !== null ? parseFloat(form.height_cm) : null;
    const weightVal = form.weight_kg !== '' && form.weight_kg !== null ? parseFloat(form.weight_kg) : null;

    updateSession({ name: trimmedName });
    const patch = {
      phone: phoneVal,
      age: ageVal,
      height_cm: heightVal,
      weight_kg: weightVal,
    };
    updateProfile(patch);
    setEditing(false);
    toast.success('Profile updated');

    try {
      await saveUserProfileAPI(user.id || user.email, {
        user_id: user.id || user.email,
        name: trimmedName,
        phone: phoneVal,
        age: ageVal,
        height_cm: heightVal,
        weight_kg: weightVal,
        diet: profile.diet,
        goal: profile.goal,
        budget: profile.budget,
        allergies: profile.allergies,
        intolerances: profile.intolerances,
        dislikes: profile.dislikes,
        restrictions: profile.restrictions,
        activity_level: profile.activity_level || 'moderately active',
      });
    } catch (err) {
      console.warn('Backend profile sync note:', err.message);
    }
  };

  const onAvatar = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (!file.type.startsWith('image/')) { toast.error('Please choose an image file.'); return; }
    if (file.size > 8 * 1024 * 1024) { toast.error('Image is too large (max 8 MB).'); return; }
    try {
      updateProfile({ avatar: await fileToThumb(file, 200) });
      toast.success('Profile photo updated');
    } catch {
      toast.error('Could not read that image.');
    }
  };

  const downloadReports = () => {
    try {
      generateActivityReportPDF({ user, profile, stats, calorieGoal, progress, activity });
      toast.success('Activity & Nutrition Report (PDF) downloaded');
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('Failed to generate PDF report');
    }
  };

  const doLogout = () => { logout(); toast.info('You have been logged out'); navigate('/', { replace: true }); };

  return (
    <div className="page profile">
      <PageHeader title="Profile & Settings" icon={User} />

      <Card className="profile-card">
        <div className="profile-card__who">
          <div className="avatar-edit">
            <Avatar name={user.name} src={profile.avatar} size={84} />
            <button className="avatar-edit__btn" onClick={() => fileRef.current?.click()} aria-label="Change profile photo"><Camera size={15} /></button>
            <input ref={fileRef} type="file" accept="image/*" hidden onChange={onAvatar} />
          </div>
          <div>
            <h2>{user.name}</h2>
            <p className="muted"><Mail size={14} /> {user.email}</p>
            {profile.phone && <p className="muted"><Phone size={14} /> {profile.phone}</p>}
          </div>
        </div>
        <Button variant="outline" size="sm" icon={Pencil} onClick={openEdit}>Edit Profile</Button>
      </Card>

      <div className="profile-grid">
        <Card padded={false} className="settings-list">
          <ul>
            {ROWS.map(({ id, label, icon: Icon }) => (
              <li key={id}>
                <button onClick={() => setPanel(id)}>
                  <span className="settings-list__ico"><Icon size={18} /></span>
                  <span>{label}</span>
                  <ChevronRight size={18} />
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <div className="profile-side">
          <Card title="Your Progress">
            <div className="progress-box">
              <ProgressRing value={progress} size={104} stroke={11} />
              <div>
                <p className="muted">Health Goal</p>
                <h3>{profile.goal}</h3>
                <span className={`pill ${progress >= 100 ? 'pill--orange' : 'pill--green'}`}>{progress >= 100 ? 'Goal reached' : 'On Track'}</span>
                <p className="muted small"><Flame size={13} /> {stats.calories} / {calorieGoal} kcal today</p>
              </div>
            </div>
          </Card>
          <Card title="Quick Links">
            <ul className="quick-links">
              <li><button onClick={downloadReports}><Download size={18} /> Download Reports (PDF)</button></li>
              <li><button className="danger" onClick={() => setConfirmLogout(true)}><LogOut size={18} /> Logout</button></li>
            </ul>
          </Card>
        </div>
      </div>

      {/* Edit profile */}
      <Modal open={editing} onClose={() => setEditing(false)} title="Edit profile" size="sm">
        <form className="form" onSubmit={saveProfile} noValidate>
          <TextField label="Full name" icon={User} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} error={errors.name} />
          <TextField label="Email" icon={Mail} value={user.email} readOnly hint="Your email is your login ID and can't be changed here." />
          <TextField label="Phone (optional)" icon={Phone} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} error={errors.phone} placeholder="+91 98765 43210" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            <TextField label="Age" type="number" placeholder="25" value={form.age || ''} onChange={(e) => setForm((f) => ({ ...f, age: e.target.value }))} error={errors.age} />
            <TextField label="Height (cm)" type="number" placeholder="172" value={form.height_cm || ''} onChange={(e) => setForm((f) => ({ ...f, height_cm: e.target.value }))} error={errors.height_cm} />
            <TextField label="Weight (kg)" type="number" placeholder="68" value={form.weight_kg || ''} onChange={(e) => setForm((f) => ({ ...f, weight_kg: e.target.value }))} error={errors.weight_kg} />
          </div>
          <div className="modal__actions"><Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button><Button type="submit">Save changes</Button></div>
        </form>
      </Modal>

      {/* Settings panels */}
      <Modal open={panel === 'account'} onClose={() => setPanel(null)} title="Account Settings"><AccountPanel changePassword={changePassword} settings={settings} updateSettings={updateSettings} toast={toast} /></Modal>
      <Modal open={panel === 'diet'} onClose={() => setPanel(null)} title="Dietary Preferences & Safety" size="sm">
        <div className="form">
          <SelectField
            label="Diet type"
            value={profile.diet}
            onChange={(v) => {
              updateProfile({ diet: v });
              toast.success(`Diet set to ${v}`);
              saveUserProfileAPI(user.id || user.email, { ...profile, diet: v }).catch(console.warn);
            }}
            options={DIETS}
          />
          <SelectField
            label="Budget"
            value={profile.budget}
            onChange={(v) => {
              updateProfile({ budget: v });
              toast.success(`Budget set to ${v}`);
              saveUserProfileAPI(user.id || user.email, { ...profile, budget: v }).catch(console.warn);
            }}
            options={BUDGETS}
          />
          <TextField
            label="Allergies (Strict Exclusions)"
            placeholder="e.g. peanuts, shellfish, tree nuts"
            value={profile.allergies || ''}
            onChange={(e) => updateProfile({ allergies: e.target.value })}
            onBlur={() => saveUserProfileAPI(user.id || user.email, { ...profile }).catch(console.warn)}
            hint="Strict safety triggers. Meals containing these will NEVER be recommended."
          />
          <TextField
            label="Food Intolerances"
            placeholder="e.g. lactose, dairy, gluten, wheat"
            value={Array.isArray(profile.intolerances) ? profile.intolerances.join(', ') : (profile.intolerances || '')}
            onChange={(e) => updateProfile({ intolerances: e.target.value })}
            onBlur={() => saveUserProfileAPI(user.id || user.email, { ...profile }).catch(console.warn)}
            hint="Digestive sensitivities. Handled separately from acute allergies."
          />
          <TextField
            label="Disliked Ingredients"
            placeholder="e.g. mushrooms, cilantro, olives"
            value={Array.isArray(profile.dislikes) ? profile.dislikes.join(', ') : (profile.dislikes || '')}
            onChange={(e) => updateProfile({ dislikes: e.target.value })}
            onBlur={() => saveUserProfileAPI(user.id || user.email, { ...profile }).catch(console.warn)}
            hint="Personal taste preferences to avoid where possible."
          />
          <TextField
            label="Dietary Restrictions"
            placeholder="e.g. halal, kosher, jain, no alcohol"
            value={Array.isArray(profile.restrictions) ? profile.restrictions.join(', ') : (profile.restrictions || '')}
            onChange={(e) => updateProfile({ restrictions: e.target.value })}
            onBlur={() => saveUserProfileAPI(user.id || user.email, { ...profile }).catch(console.warn)}
            hint="Religious or ethical guidelines."
          />
        </div>
      </Modal>
      <Modal open={panel === 'goals'} onClose={() => setPanel(null)} title="Health Goals" size="sm">
        <div className="form">
          <div className="goal-options" role="radiogroup" aria-label="Health goal">
            {GOALS.map((g) => (
              <button
                key={g}
                role="radio"
                aria-checked={profile.goal === g}
                className={`goal-opt ${profile.goal === g ? 'is-on' : ''}`}
                onClick={() => {
                  updateProfile({ goal: g });
                  toast.success(`Goal set to ${g}`);
                  saveUserProfileAPI(user.id || user.email, { ...profile, goal: g }).catch(console.warn);
                }}
              >
                <strong>{g}</strong><small>{GOAL_CALORIES[g]?.toLocaleString() || 1900} kcal/day</small>
              </button>
            ))}
          </div>
          <p className="muted small" style={{ marginTop: '12px', lineHeight: '1.4' }}>
            ℹ️ Daily calorie targets are algorithmic reference estimates based on demographic guidelines and not clinical prescriptions.
          </p>
        </div>
      </Modal>
      <Modal open={panel === 'notifications'} onClose={() => setPanel(null)} title="Notification Settings" size="sm">
        <div className="toggle-list">
          <Toggle label="Meal reminders" description="Gentle nudges at breakfast, lunch and dinner" checked={settings.mealReminders} onChange={(v) => updateSettings({ mealReminders: v })} />
          <Toggle label="Freshness alerts" description="Warn me when food may be spoiling" checked={settings.freshnessAlerts} onChange={(v) => updateSettings({ freshnessAlerts: v })} />
          <Toggle label="Weekly report" description="A summary of your week every Sunday" checked={settings.weeklyReport} onChange={(v) => updateSettings({ weeklyReport: v })} />
          <Toggle label="Product updates" description="News about new Food Verse AI features" checked={settings.emailUpdates} onChange={(v) => updateSettings({ emailUpdates: v })} />
        </div>
      </Modal>
      <Modal open={panel === 'help'} onClose={() => setPanel(null)} title="Help & Support"><HelpPanel toast={toast} onDone={() => setPanel(null)} /></Modal>
      <Modal open={panel === 'about'} onClose={() => setPanel(null)} title="About Food Verse AI" size="sm">
        <div className="about">
          <LeafMark size={56} />
          <h3>Food Verse AI</h3>
          <p className="muted">Smart Food. Healthier You.</p>
          <p>Food Verse AI helps you identify food, check freshness, review kitchen hygiene, cook with what you have and plan healthy weeks.</p>
          <p className="note-box"><Info size={16} /> This is a frontend demo using mock data. Results are illustrative and not medical or food-safety advice.</p>
          <small className="muted">Version 1.0.0</small>
        </div>
      </Modal>

      <Modal open={confirmLogout} onClose={() => setConfirmLogout(false)} title="Log out?" size="sm"
        footer={<><Button variant="outline" onClick={() => setConfirmLogout(false)}>Stay</Button><Button variant="danger" icon={LogOut} onClick={doLogout}>Log out</Button></>}>
        <p>You'll need to log in again to access your dashboard.</p>
      </Modal>
    </div>
  );
}

function AccountPanel({ changePassword, settings, updateSettings, toast }) {
  const [pw, setPw] = useState({ current: '', next: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const errs = {
      current: pw.current ? '' : 'Enter your current password',
      next: validatePassword(pw.next) || (pw.next === pw.current ? 'New password must be different' : ''),
      confirm: pw.confirm === pw.next ? '' : 'Passwords do not match',
    };
    setErrors(errs);
    if (Object.values(errs).some(Boolean)) return;
    setBusy(true);
    try {
      await changePassword({ current: pw.current, next: pw.next });
      toast.success('Password updated');
      setPw({ current: '', next: '', confirm: '' });
    } catch (err) {
      setErrors({ current: err.message });
    } finally {
      setBusy(false);
    }
  };

  const resetData = () => {
    if (!window.confirm('Reset all saved preferences, meal plan and activity on this device?')) return;
    Object.keys(localStorage).filter((k) => k.startsWith('fv_appdata')).forEach((k) => localStorage.removeItem(k));
    toast.success('Local data cleared. Reloading…');
    setTimeout(() => window.location.reload(), 700);
  };

  return (
    <div className="form">
      <h4 className="subhead">Change password</h4>
      <form className="form" onSubmit={submit} noValidate>
        <TextField label="Current password" type="password" icon={Lock} value={pw.current} onChange={(e) => setPw((p) => ({ ...p, current: e.target.value }))} error={errors.current} autoComplete="current-password" />
        <TextField label="New password" type="password" icon={Lock} value={pw.next} onChange={(e) => setPw((p) => ({ ...p, next: e.target.value }))} error={errors.next} autoComplete="new-password" />
        <TextField label="Confirm new password" type="password" icon={Lock} value={pw.confirm} onChange={(e) => setPw((p) => ({ ...p, confirm: e.target.value }))} error={errors.confirm} autoComplete="new-password" />
        <Button type="submit" loading={busy}>Update password</Button>
      </form>
      <h4 className="subhead">Display</h4>
      <Toggle label="Compact layout" description="Tighter spacing to fit more on screen" checked={settings.compactMode} onChange={(v) => updateSettings({ compactMode: v })} />
      <h4 className="subhead">Data</h4>
      <Button variant="danger" icon={Trash2} onClick={resetData}>Reset local data</Button>
    </div>
  );
}

function HelpPanel({ toast, onDone }) {
  const [open, setOpen] = useState(0);
  const [msg, setMsg] = useState({ email: '', text: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  const send = async (e) => {
    e.preventDefault();
    const errs = { email: validateEmail(msg.email), text: msg.text.trim().length < 10 ? 'Please describe your question (at least 10 characters)' : '' };
    setErrors(errs);
    if (errs.email || errs.text) return;
    setBusy(true);
    await new Promise((r) => setTimeout(r, 800));
    setBusy(false);
    toast.success("Message sent! We'll reply within 1–2 business days.");
    onDone();
  };

  return (
    <div className="help">
      <h4 className="subhead">Frequently asked</h4>
      <ul className="faq">
        {HELP_FAQ.map((f, i) => (
          <li key={f.q} className={open === i ? 'is-open' : ''}>
            <button onClick={() => setOpen(open === i ? -1 : i)} aria-expanded={open === i}>{f.q}<ChevronDown size={18} /></button>
            {open === i && <p>{f.a}</p>}
          </li>
        ))}
      </ul>
      <h4 className="subhead">Contact support</h4>
      <form className="form" onSubmit={send} noValidate>
        <TextField label="Your email" type="email" icon={Mail} value={msg.email} onChange={(e) => setMsg((m) => ({ ...m, email: e.target.value }))} error={errors.email} />
        <div className={`field ${errors.text ? 'field--error' : ''}`}>
          <label htmlFor="help-msg">Message</label>
          <div className="field__control"><textarea id="help-msg" rows={4} value={msg.text} onChange={(e) => setMsg((m) => ({ ...m, text: e.target.value }))} placeholder="How can we help?" /></div>
          {errors.text && <p className="field__error" role="alert">{errors.text}</p>}
        </div>
        <Button type="submit" icon={Send} loading={busy}>Send message</Button>
      </form>
    </div>
  );
}
