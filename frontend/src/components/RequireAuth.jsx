// src/components/RequireAuth.jsx
// Wraps protected routes — redirects unauthenticated users to /login
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Wait for token rehydration before deciding
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Save where the user was trying to go so we can redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
