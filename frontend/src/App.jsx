import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import RequireAuth from './components/RequireAuth';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import Analytics from './pages/Analytics';
import History from './pages/History';
import Alerts from './pages/Alerts';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Compare from './pages/Compare';
import PathogenExplorer from './pages/PathogenExplorer';
import BulkImport from './pages/BulkImport';
import CompareAnalytics from './pages/CompareAnalytics';
import DataQuality from './pages/DataQuality';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route — login page */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes — wrapped in auth guard */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="predict" element={<Predict />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="history" element={<History />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
          <Route path="compare" element={<Compare />} />
          <Route path="pathogen-explorer" element={<PathogenExplorer />} />
          <Route path="bulk-import" element={<BulkImport />} />
          <Route path="compare-analytics" element={<CompareAnalytics />} />
          <Route path="data-quality" element={<DataQuality />} />
        </Route>

        {/* Catch-all: redirect unknown paths to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}