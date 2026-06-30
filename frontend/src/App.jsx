/**
 * App.jsx — AMR-Nexus Root Application v2.2
 *
 * Changes:
 *  1. ErrorBoundary wraps entire app to catch render-time crashes (Black Screen fix)
 *  2. RBAC routing: National Coordinator + Policy Maker → /national
 *                   County Veterinarian + County Clinician + Lab Technician → /county
 *  3. /national and /county explicit routes (not just index)
 *  4. Loading spinner matches dark theme (no plain "Loading Application..." text)
 *  5. Debug console.log removed from production code
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth }   from './contexts/AuthContext';
import ErrorBoundary               from './components/ErrorBoundary';
import Layout                      from './components/Layout/Layout';

// ── Pages ─────────────────────────────────────────────────────────────────────
import Login              from './pages/Login';
import NationalDashboard  from './pages/NationalDashboard';
import CountyDashboard    from './pages/CountyDashboard';
import Predict            from './pages/Predict';
import Analytics          from './pages/Analytics';
import History            from './pages/History';
import Alerts             from './pages/Alerts';
import Reports            from './pages/Reports';
import Settings           from './pages/Settings';
import Compare            from './pages/Compare';
import PathogenExplorer   from './pages/PathogenExplorer';
import BulkImport         from './pages/BulkImport';
import CompareAnalytics   from './pages/CompareAnalytics';
import DataQuality        from './pages/DataQuality';

// ── RBAC Role Groups ──────────────────────────────────────────────────────────

const NATIONAL_ROLES = new Set(['National Coordinator', 'Policy Maker']);
const COUNTY_ROLES   = new Set(['County Veterinarian', 'County Clinician', 'Lab Technician']);

// ── Loading Screen ────────────────────────────────────────────────────────────

function AppLoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-full border-4 border-blue-600 border-t-transparent animate-spin" />
        <p className="text-blue-300 text-sm animate-pulse">Loading AMR-Nexus…</p>
      </div>
    </div>
  );
}

// ── Route Tree ────────────────────────────────────────────────────────────────

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <AppLoadingScreen />;

  // Unauthenticated: only /login is accessible
  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*"      element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // Determine default dashboard based on role
  const isNational = NATIONAL_ROLES.has(user.role);
  const defaultDash = isNational ? <NationalDashboard /> : <CountyDashboard />;

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        {/* Default: redirect to role-appropriate dashboard */}
        <Route index element={<Navigate to={isNational ? '/national' : '/county'} replace />} />

        {/* National Coordinator / Policy Maker */}
        <Route path="national" element={
          isNational ? <NationalDashboard /> : <Navigate to="/county" replace />
        } />

        {/* County Veterinarian / County Clinician / Lab Technician */}
        <Route path="county" element={
          COUNTY_ROLES.has(user.role) ? <CountyDashboard /> : <Navigate to="/national" replace />
        } />

        {/* Shared — all authenticated roles */}
        <Route path="dashboard"         element={defaultDash} />
        <Route path="predict"           element={<Predict />} />
        <Route path="analytics"         element={<Analytics />} />
        <Route path="history"           element={<History />} />
        <Route path="alerts"            element={<Alerts />} />
        <Route path="reports"           element={<Reports />} />
        <Route path="settings"          element={<Settings />} />
        <Route path="compare"           element={<Compare />} />
        <Route path="pathogen-explorer" element={<PathogenExplorer />} />
        <Route path="bulk-import"       element={<BulkImport />} />
        <Route path="compare-analytics" element={<CompareAnalytics />} />
        <Route path="data-quality"      element={<DataQuality />} />
      </Route>

      {/* Fallback: authenticated users go to dashboard */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ── Root Component ─────────────────────────────────────────────────────────────

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}