import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScanForm from '../components/ScanForm';
import { submitScan, getStats } from '../api/client';
import type { ScanResponse } from '../types';

export default function HomePage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [totalScans, setTotalScans] = useState<number | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await getStats();
        setTotalScans(data.total_scans);
      } catch {
        /* silently ignore — counter just won't show */
      }
    }

    fetchStats();
    const interval = setInterval(fetchStats, 600000);
    return () => clearInterval(interval);
  }, []);

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
      {/* Brand mark — fixed top-left */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        zIndex: 10,
      }}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="var(--accent)" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5Z" />
        </svg>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: 22,
          color: 'var(--text-primary)',
          lineHeight: 1,
        }}>
          ShieldScan
        </span>
      </div>

      {/* Version & Stats — fixed top-right */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        padding: '24px 28px',
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-muted)',
      }}>
        {totalScans !== null && (
          <>
            <span className="pulse-dot" />
            <span>{totalScans.toLocaleString()} SITES ANALYZED</span>
            <span>|</span>
          </>
        )}
        <span>v1.0.0</span>
      </div>

      {/* Center content */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 32px',
        gap: 40,
        marginTop: -60,
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

        {/* Scan form */}
        <ScanForm onSubmit={handleScan} isLoading={isLoading} />

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
