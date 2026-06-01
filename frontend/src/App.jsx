import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './components/layout/AppLayout';
import NationalOverview from './pages/NationalOverview';
import NationalMap from './pages/NationalMap';
import NationalTrends from './pages/NationalTrends';
import NationalAlerts from './pages/NationalAlerts';
import NationalGuidance from './pages/NationalGuidance';
import CountyOverview from './pages/CountyOverview';
import CountyAlerts from './pages/CountyAlerts';
import CountyGuidance from './pages/CountyGuidance';

const queryClient = new QueryClient();

export default function App() {
  const [role, setRole] = useState('national');
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route element={
          <AppLayout
            role={role}
            onToggleRole={() => setRole(r => r === 'national' ? 'county' : 'national')}
            darkMode={darkMode}
            onToggleDark={() => setDarkMode(d => !d)}
          />
        }>
          <Route path="/" element={<Navigate to="/national" replace />} />
          {/* Pass darkMode to ALL pages that contain the map */}
          <Route path="/national" element={<NationalOverview role={role} darkMode={darkMode} />} />
          <Route path="/national/map" element={<NationalMap role={role} darkMode={darkMode} />} />
          <Route path="/national/trends" element={<NationalTrends />} />
          <Route path="/national/alerts" element={<NationalAlerts role={role} />} />
          <Route path="/national/guidance" element={<NationalGuidance />} />
          <Route path="/county" element={<CountyOverview role={role} />} />
          <Route path="/county/alerts" element={<CountyAlerts role={role} />} />
          <Route path="/county/guidance" element={<CountyGuidance />} />
        </Route>
      </Routes>
    </QueryClientProvider>
  );
}