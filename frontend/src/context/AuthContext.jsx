/**
 * context/AuthContext.jsx — AMR-Nexus Authentication Context
 *
 * Provides:
 *  - login(username, password) → calls real /api/v1/token endpoint
 *  - logout() → clears token + redirects
 *  - user { username, role } decoded from stored JWT claims
 *  - token — raw JWT string (for any component that needs it)
 *  - isAuthenticated — boolean
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

function decodeJWT(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('amr_token'));
  const [loading, setLoading] = useState(true);

  // Rehydrate user from stored token on mount
  useEffect(() => {
    const stored = localStorage.getItem('amr_token');
    if (stored) {
      const claims = decodeJWT(stored);
      if (claims && claims.exp * 1000 > Date.now()) {
        setToken(stored);
        setUser({ username: claims.sub, role: claims.role });
      } else {
        // Token expired — clean up
        localStorage.removeItem('amr_token');
        localStorage.removeItem('amr_user');
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password);
    const claims = decodeJWT(data.access_token);
    const userData = {
      username: claims?.sub ?? username,
      role: claims?.role ?? 'National Coordinator',
    };
    setToken(data.access_token);
    setUser(userData);
    localStorage.setItem('amr_user', JSON.stringify(userData));
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('amr_token');
    localStorage.removeItem('amr_user');
    setToken(null);
    setUser(null);
    api.logout();
  }, []);

  // Convenience: expose role-switching for settings page (local only)
  const setRole = useCallback((role) => {
    setUser((prev) => prev ? { ...prev, role } : { username: 'demo', role });
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      isAuthenticated: !!token,
      login,
      logout,
      setRole,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
