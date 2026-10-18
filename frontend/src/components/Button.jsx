import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

/**
 * variant: primary (green) | accent (orange) | outline | ghost | danger
 * Renders a <Link> when `to` is passed, otherwise a <button>.
 */
export default function Button({
  variant = 'primary', size = 'md', icon: Icon, iconRight: IconRight, loading = false,
  block = false, to, className = '', children, disabled, type = 'button', ...rest
}) {
  const cls = `btn btn--${variant} btn--${size} ${block ? 'btn--block' : ''} ${className}`;
  const inner = (
    <>
      {loading ? <Loader2 size={18} className="spin" /> : Icon && <Icon size={size === 'sm' ? 16 : 18} />}
      {children && <span>{children}</span>}
      {!loading && IconRight && <IconRight size={size === 'sm' ? 16 : 18} />}
    </>
  );
  if (to && !disabled) return <Link to={to} className={cls} {...rest}>{inner}</Link>;
  return (
    <button type={type} className={cls} disabled={disabled || loading} {...rest}>
      {inner}
    </button>
  );
}
