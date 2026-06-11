import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ScanForm from '../components/ScanForm';
import { submitScan, getCredits } from '../api/client';
import type { ScanResponse } from '../types';

export default function HomePage() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [credits, setCredits] = useState<number | null>(null);


  useEffect(() => {
    if (!user) {
      setCredits(null);
      return;
    }

    async function fetchCredits() {
      try {
        const data = await getCredits();
        setCredits(data.credits_remaining);
      } catch {
        /* silently ignore */
      }
    }

    fetchCredits();
  }, [user]);

  async function handleScan(url: string) {
    setIsLoading(true);
    setError('');

    try {
      const result: ScanResponse = await submitScan(url);
      navigate(`/result/${result.id}`, { state: { scanData: result } });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page-container">
      {/* Center content */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 32px',
        gap: 40,
        marginTop: 0,
      }}>
        {/* Heading */}
        <div style={{ textAlign: 'center', maxWidth: 700 }}>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(40px, 6vw, 72px)',
            fontWeight: 400,
            lineHeight: 1.1,
            color: 'var(--text-primary)',
            marginBottom: 20,
          }}>
            Security Analysis,<br />
            Without the Noise.
          </h1>
          <p style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 16,
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
          }}>
            Enter any URL. Get a detailed security audit in seconds.
          </p>
        </div>

        {/* Scan form or sign-in prompt */}
        {!authLoading && !user ? (
          <div style={{ textAlign: 'center' }}>
            <Link to="/login" className="home-signin-btn">
              SIGN IN TO SCAN →
            </Link>
            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--text-muted)',
              marginTop: 12,
            }}>
              Create a free account to start scanning
            </p>
          </div>
        ) : (
          <>
            <ScanForm onSubmit={handleScan} isLoading={isLoading} />

            {/* Credits info */}
            {user && credits !== null && (
              <div className="home-credits-info">
                <span className="credits-badge">
                  {credits} credit{credits !== 1 ? 's' : ''} remaining
                </span>
              </div>
            )}
          </>
        )}

        {/* Error */}
        {error && (
          <p className="error-msg">{error}</p>
        )}

        {/* Feature pills */}
        <div className="feature-pills">
          <span className="feature-pill">SSL CERTIFICATE</span>
          <span className="feature-pill">SECURITY HEADERS</span>
          <span className="feature-pill">AI EXPLANATIONS</span>
        </div>
      </div>
    </div>
  );
}
