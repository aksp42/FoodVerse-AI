import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function PageHeader({ title, subtitle, icon: Icon, actions }) {
  const navigate = useNavigate();
  const location = useLocation();
  // `key` is "default" on the first page of the session — then go to the dashboard instead.
  const goBack = () => (location.key === 'default' ? navigate('/app') : navigate(-1));
  return (
    <div className="page-head">
      <button className="icon-btn page-head__back" onClick={goBack} aria-label="Go back"><ArrowLeft size={20} /></button>
      <div className="page-head__text">
        <h1>{Icon && <Icon size={24} className="page-head__ico" />} {title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="page-head__actions">{actions}</div>}
    </div>
  );
}
