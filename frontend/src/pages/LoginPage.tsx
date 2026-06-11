import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

type Mode = 'signin' | 'signup';

export default function LoginPage() {
  const navigate = useNavigate();
  const { signIn, signUp } = useAuth();

  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (mode === 'signin') {
        const { error: err } = await signIn(email, password);
        if (err) {
          setError(err);
        } else {
          navigate('/');
        }
      } else {
        const { error: err } = await signUp(email, password);
        if (err) {
          setError(err);
        } else {
          setSuccessMsg('Check your email to confirm your account, then sign in.');
        }
      }
    } catch {
      setError('An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }

  function toggleMode() {
    setMode(mode === 'signin' ? 'signup' : 'signin');
    setError('');
    setSuccessMsg('');
  }

  return (
    <div className="page-container" style={{ paddingTop: 80 }}>
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 24px',
      }}>
        <div className="auth-card">
          {/* Shield icon */}
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="var(--accent)" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5Z" />
            </svg>
          </div>

          <h2 className="auth-title">
            {mode === 'signin' ? 'Welcome back' : 'Create account'}
          </h2>
          <p className="auth-subtitle">
            {mode === 'signin'
              ? 'Sign in to access your scan history'
              : 'Get started with ShieldScan'}
          </p>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-email">EMAIL</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="auth-input"
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-password">PASSWORD</label>
              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="auth-input"
                required
                minLength={6}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              />
            </div>

            {error && <p className="auth-error">{error}</p>}
            {successMsg && <p className="auth-success">{successMsg}</p>}

            <button
              type="submit"
              className="auth-button"
              disabled={loading}
            >
              {loading
                ? (mode === 'signin' ? 'SIGNING IN...' : 'CREATING ACCOUNT...')
                : (mode === 'signin' ? 'SIGN IN →' : 'CREATE ACCOUNT →')
              }
            </button>
          </form>

          <div className="auth-footer">
            <span className="auth-footer-text">
              {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}
            </span>
            <button className="auth-toggle" onClick={toggleMode}>
              {mode === 'signin' ? 'Sign up' : 'Sign in'}
            </button>
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Link to="/" className="auth-back-link">
              ← Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
