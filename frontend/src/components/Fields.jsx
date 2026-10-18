import { forwardRef, useId, useState } from 'react';
import { Eye, EyeOff, ChevronDown } from 'lucide-react';

export const TextField = forwardRef(function TextField(
  { label, error, hint, icon: Icon, type = 'text', className = '', ...rest }, ref,
) {
  const id = useId();
  const [show, setShow] = useState(false);
  const isPw = type === 'password';
  return (
    <div className={`field ${error ? 'field--error' : ''} ${className}`}>
      {label && <label htmlFor={id}>{label}</label>}
      <div className="field__control">
        {Icon && <Icon size={18} className="field__icon" />}
        <input
          id={id} ref={ref} type={isPw && show ? 'text' : type}
          aria-invalid={!!error} aria-describedby={error ? `${id}-err` : undefined}
          className={Icon ? 'has-icon' : ''} {...rest}
        />
        {isPw && (
          <button type="button" className="field__toggle" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'}>
            {show ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {error ? <p className="field__error" id={`${id}-err`} role="alert">{error}</p> : hint && <p className="field__hint">{hint}</p>}
    </div>
  );
});

export function SelectField({ label, value, onChange, options, className = '', ...rest }) {
  const id = useId();
  return (
    <div className={`field ${className}`}>
      {label && <label htmlFor={id}>{label}</label>}
      <div className="field__control field__control--select">
        <select id={id} value={value} onChange={(e) => onChange(e.target.value)} {...rest}>
          {options.map((o) => {
            const v = typeof o === 'string' ? o : o.value;
            const l = typeof o === 'string' ? o : o.label;
            return <option key={v} value={v}>{l}</option>;
          })}
        </select>
        <ChevronDown size={18} className="field__chev" />
      </div>
    </div>
  );
}

export function Toggle({ checked, onChange, label, description }) {
  const id = useId();
  return (
    <div className="toggle-row">
      <label htmlFor={id} className="toggle-row__text">
        <strong>{label}</strong>
        {description && <span>{description}</span>}
      </label>
      <button
        id={id} type="button" role="switch" aria-checked={checked}
        className={`toggle ${checked ? 'toggle--on' : ''}`} onClick={() => onChange(!checked)}
      >
        <span className="toggle__knob" />
      </button>
    </div>
  );
}
