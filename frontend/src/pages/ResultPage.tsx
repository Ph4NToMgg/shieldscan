import { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import ScoreCard from '../components/ScoreCard';
import CheckItem from '../components/CheckItem';
import { getScan } from '../api/client';
import type { ScanResponse, AISummary, AIExplanation } from '../types';

interface LocationState {
  scanData?: ScanResponse;
}

function parseAISummary(aiSummaryStr: string | null): AISummary | null {
  if (!aiSummaryStr) return null;
  try {
    const parsed: AISummary = JSON.parse(aiSummaryStr);
    if (parsed.overall_summary && Array.isArray(parsed.explanations)) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

function findExplanation(
  explanations: AIExplanation[],
  checkName: string,
): AIExplanation | undefined {
  return explanations.find(
    (e) => e.check_name.toLowerCase().includes(checkName.toLowerCase()),
  );
}

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const locationState = location.state as LocationState | null;

  const [scanData, setScanData] = useState<ScanResponse | null>(
    locationState?.scanData ?? null,
  );
  const [isLoading, setIsLoading] = useState(!scanData);
  const [error, setError] = useState('');

  useEffect(() => {
    if (scanData || !id) return;

    async function fetchScan() {
      try {
        const result = await getScan(id!);
        setScanData(result);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to load scan results.');
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchScan();
  }, [id, scanData]);

  /* Loading state */
  if (isLoading) {
    return (
      <div className="page-container" style={{
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          color: 'var(--text-muted)',
          letterSpacing: '0.1em',
        }}>
          LOADING<span className="blink-cursor">_</span>
        </span>
      </div>
    );
  }

  /* Error state */
  if (error || !scanData) {
    return (
      <div className="page-container" style={{
        alignItems: 'center',
        justifyContent: 'center',
        gap: 24,
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: 48,
          color: 'var(--status-critical)',
        }}>
          404
        </span>
        <p style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          color: 'var(--text-secondary)',
        }}>
          {error || 'Scan not found.'}
        </p>
        <Link
          to="/"
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.1em',
            color: 'var(--accent)',
          }}
        >
          ← BACK TO SCANNER
        </Link>
      </div>
    );
  }

  const { results, ai_summary } = scanData;
  const aiData = parseAISummary(ai_summary);
  const explanations = aiData?.explanations ?? [];

  return (
    <div className="page-container">
      <div className="content-max" style={{ paddingTop: 0, paddingBottom: 48 }}>
        {/* Top bar */}
        <div className="top-bar">
          <Link to="/" className="top-bar-link">
            ← NEW SCAN
          </Link>
          <div className="top-bar-url">
            <span className="small-caps-label" style={{ display: 'block', marginBottom: 2 }}>
              SCANNED
            </span>
            {results.url}
          </div>
        </div>

        {/* Score section */}
        <div style={{ marginTop: 24 }}>
          <ScoreCard
            score={results.score}
            totalChecks={results.summary.total_checks}
            passed={results.summary.passed}
            failed={results.summary.failed}
          />
        </div>

        {/* AI Summary */}
        {aiData?.overall_summary && (
          <div style={{ marginTop: 48 }}>
            <div className="small-caps-label" style={{ marginBottom: 12 }}>
              AI ASSESSMENT
            </div>
            <div className="ai-summary">
              <p className="ai-summary-text">
                {aiData.overall_summary}
              </p>
            </div>
          </div>
        )}

        {/* Detailed Results */}
        <div style={{ marginTop: 48 }}>
          <div className="section-header">
            DETAILED RESULTS
          </div>

          {/* SSL */}
          <CheckItem
            name="SSL Certificate"
            passed={results.ssl.passed}
            detail={results.ssl.detail}
            severity={results.ssl.severity}
            aiExplanation={findExplanation(explanations, 'ssl')}
          />

          {/* HTTPS Redirect */}
          <CheckItem
            name="HTTP → HTTPS Redirect"
            passed={results.redirect.passed}
            detail={results.redirect.detail}
            severity={results.redirect.severity}
            aiExplanation={findExplanation(explanations, 'redirect')}
          />

          {/* Security Headers */}
          {results.headers.map((header) => (
            <CheckItem
              key={header.name}
              name={header.name}
              passed={header.passed}
              detail={header.detail}
              severity={header.severity}
              aiExplanation={findExplanation(explanations, header.name)}
            />
          ))}
        </div>

        {/* Footer metadata */}
        <div className="meta-footer" style={{ marginTop: 48 }}>
          <span>SCAN ID: {scanData.id}</span>
          <span>COMPLETED: {new Date(scanData.created_at).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
