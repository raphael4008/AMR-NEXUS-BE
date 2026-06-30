// import { createContext, useContext, useState, useEffect } from 'react';
// import api from '../api/client'; // Use your centralized axios instance

// const AuthContext = createContext();

// export function AuthProvider({ children }) {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);

//   useEffect(() => {
//     const initializeAuth = async () => {
//       const token = localStorage.getItem('token');
//       if (!token) {
//         setLoading(false);
//         return; // Stay unauthenticated, App.jsx will redirect to /login
//       }

//       try {
//         // Validate token with backend
//         const data = await api.getMe(); // Calls /api/v1/users/me
//         setUser(data);
//       } catch (err) {
//         console.error('Session expired or invalid:', err);
//         localStorage.clear();
//         setUser(null);
//       } finally {
//         setLoading(false);
//       }
//     };

//     initializeAuth();
//   }, []);

//   const login = async (email, password) => {
//     setLoading(true);
//     try {
//       // Use your bridge endpoint
//       const response = await api.post('/auth/login', { email, password });
//       const { token, user: userData } = response.data;
      
//       localStorage.setItem('token', token);
//       setUser(userData);
//       setError(null);
//     } catch (err) {
//       setError('Invalid email or password');
//       throw err;
//     } finally {
//       setLoading(false);
//     }
//   };

//   const logout = () => {
//     localStorage.clear();
//     setUser(null);
//     window.location.href = '/login';
//   };

//   return (
//     <AuthContext.Provider
//       value={{
//         user,
//         loading,
//         error,
//         login,
//         logout,
//         isAuthenticated: !!user,
//       }}
//     >
//       {children}
//     </AuthContext.Provider>
//   );
// }

// export const useAuth = () => useContext(AuthContext);
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
// Import your Login component
import Login from './pages/Login'; 
import Dashboard from './pages/Dashboard';
import NationalDashboard from './pages/NationalDashboard';
import CountyDashboard from './pages/CountyDashboard';
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

function AppRoutes() {
  const { user, loading } = useAuth();

  // Show a simple loader while checking auth state
  if (loading) return <div>Loading Application...</div>;

  // If no user is authenticated, redirect to Login
  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const isNational = user?.role === 'National Coordinator';

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={isNational ? <NationalDashboard /> : <CountyDashboard />} />
        <Route path="dashboard" element={isNational ? <NationalDashboard /> : <CountyDashboard />} />
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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}