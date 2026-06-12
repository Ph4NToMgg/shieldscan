import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import LoginPage from './pages/LoginPage';
import HistoryPage from './pages/HistoryPage';
import { getStats } from './api/client';

export default function App() {
  const [totalScans, setTotalScans] = useState<number | null>(null);

  useEffect(() => {
    // Fetch stats immediately (also wakes up Render)
    async function fetchStats() {
      try {
        const data = await getStats();
        setTotalScans(data.total_scans);
      } catch {
        /* server might be waking up */
      }
    }

    fetchStats();

    // Keep-alive ping every 10 minutes to prevent Render free tier from sleeping
    const keepAlive = setInterval(fetchStats, 10 * 60 * 1000);

    return () => clearInterval(keepAlive);
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/result/:id" element={<ResultPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>

        {/* Total scans footer */}
        {totalScans !== null && (
          <div className="stats-footer">
            <span className="stats-pulse" />
            <span className="stats-text">
              {totalScans.toLocaleString()} scan{totalScans !== 1 ? 's' : ''} performed
            </span>
          </div>
        )}
      </AuthProvider>
    </BrowserRouter>
  );
}

