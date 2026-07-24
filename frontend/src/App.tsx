import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import LoginPage from './pages/LoginPage';
import HistoryPage from './pages/HistoryPage';
import AetherBackground from './components/AetherBackground';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AetherBackground />
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/result/:id" element={<ResultPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

