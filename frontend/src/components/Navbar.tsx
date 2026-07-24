import { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getCredits, getStats } from '../api/client';

export default function Navbar() {
  const { user, loading, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [credits, setCredits] = useState<number | null>(null);
  const [totalScans, setTotalScans] = useState<number | null>(null);

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
  }, [user, location.pathname]);

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await getStats();
        setTotalScans(data.total_scans);
      } catch {
        /* server might be waking up */
      }
    }

    fetchStats();

    const keepAlive = setInterval(fetchStats, 10 * 60 * 1000);
    return () => clearInterval(keepAlive);
  }, [location.pathname]);

  const [waveEnabled, setWaveEnabled] = useState(
    () => localStorage.getItem('shieldscan_wave_enabled') !== 'false'
  );

  function toggleWave() {
    const next = !waveEnabled;
    setWaveEnabled(next);
    localStorage.setItem('shieldscan_wave_enabled', String(next));
    window.dispatchEvent(new Event('shieldscan_wave_toggle'));
  }

  async function handleLogout() {
    await signOut();
    navigate('/');
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Left: Brand */}
        <Link to="/" className="navbar-brand">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="var(--accent)" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5Z" />
          </svg>
          <span className="navbar-brand-text">ShieldScan</span>
        </Link>

        {/* Center: Nav links */}
        <div className="navbar-links">
          {user && (
            <Link to="/history" className="navbar-link">
              History
            </Link>
          )}
          <button
            type="button"
            className="navbar-bg-toggle"
            onClick={toggleWave}
            title="Toggle glowing wave/tail animation"
          >
            {waveEnabled ? '✨ TAIL ON' : '💤 TAIL OFF'}
          </button>
          {totalScans !== null && (
            <div className="navbar-stats">
              <span className="stats-pulse" />
              <span className="stats-text">
                {totalScans.toLocaleString()} scan{totalScans !== 1 ? 's' : ''} performed
              </span>
            </div>
          )}
        </div>

        {/* Right: Auth section */}
        <div className="navbar-right">
          {loading ? (
            <div className="navbar-skeleton" />
          ) : user ? (
            <>
              {credits !== null && (
                <span className="credits-badge">
                  {credits} credit{credits !== 1 ? 's' : ''}
                </span>
              )}
              <span className="navbar-email">{user.email}</span>
              <button className="navbar-logout" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/login" className="navbar-signin">
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
