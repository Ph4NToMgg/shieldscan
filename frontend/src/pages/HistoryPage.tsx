import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getHistory } from '../api/client';
import type { ScanResponse } from '../types';

function scoreColor(score: number): string {
  if (score >= 80) return 'var(--score-excellent)';
  if (score >= 60) return 'var(--score-good)';
  if (score >= 40) return 'var(--score-fair)';
  return 'var(--score-critical)';
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [scans, setScans] = useState<ScanResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (!user) return;

    async function fetchHistory() {
      try {
        const data = await getHistory();
        setScans(data);
      } catch {
        setError('Failed to load scan history.');
      } finally {
        setLoading(false);
      }
    }

    fetchHistory();
  }, [user]);

  if (authLoading || (!user && !authLoading)) {
    return (
      <div className="page-container" style={{ paddingTop: 80 }}>
        <div className="history-loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="page-container" style={{ paddingTop: 80 }}>
      <div className="history-container">
        <div className="history-header">
          <h1 className="history-title">Scan History</h1>
          <p className="history-subtitle">Your previous security scans</p>
        </div>

        {loading && (
          <div className="history-loading">
            <span className="history-loading-text">
              LOADING<span className="blink-cursor">_</span>
            </span>
          </div>
        )}

        {error && <p className="error-msg">{error}</p>}

        {!loading && !error && scans.length === 0 && (
          <div className="history-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5Z" />
            </svg>
            <p className="history-empty-text">No scans yet</p>
            <p className="history-empty-sub">
              Go to the <a href="/" className="history-link">home page</a> to run your first scan.
            </p>
          </div>
        )}

        {!loading && !error && scans.length > 0 && (
          <div className="history-table-wrapper">
            <table className="history-table">
              <thead>
                <tr>
                  <th>URL</th>
                  <th>SCORE</th>
                  <th>DATE</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((scan) => (
                  <tr
                    key={scan.id}
                    onClick={() => navigate(`/result/${scan.id}`)}
                    className="history-row"
                  >
                    <td className="history-cell-url">
                      <span className="history-url-text">{scan.url}</span>
                    </td>
                    <td>
                      <span
                        className="history-score"
                        style={{ color: scoreColor(scan.score) }}
                      >
                        {scan.score}
                      </span>
                    </td>
                    <td className="history-cell-date">
                      {formatDate(scan.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
