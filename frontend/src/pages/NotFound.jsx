import { Compass, Home, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';

export default function NotFound({ inApp = false }) {
  const { isAuthed } = useAuth();
  const navigate = useNavigate();
  return (
    <div className={`notfound ${inApp ? 'notfound--in' : ''}`}>
      <span className="notfound__icon"><Compass size={40} /></span>
      <h1>404</h1>
      <h2>This page isn't on the menu</h2>
      <p>The page you're looking for doesn't exist or has moved.</p>
      <div className="notfound__actions">
        <Button to={isAuthed ? '/app' : '/'} icon={Home}>{isAuthed ? 'Go to dashboard' : 'Back to home'}</Button>
        <Button variant="outline" icon={ArrowLeft} onClick={() => navigate(-1)}>Go back</Button>
      </div>
    </div>
  );
}
