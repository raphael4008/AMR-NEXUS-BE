/**
 * AuthContext.jsx — AMR-Nexus Authentication Context v2.2
 *
 * Flow:
 *  1. On mount: attempt to restore session from localStorage
 *  2. If token exists → call GET /users/me to hydrate full user object
 *  3. login():  POST /auth/token → GET /users/me → persist both
 *  4. logout(): clear localStorage, reset state
 *  5. useAuth() hook for any component to consume context
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';

// ── Context & Hook ────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // Full profile: { username, name, email, role, county }
  const [loading, setLoading] = useState(true); // True while restoring session on mount

  // ── Session Restore ───────────────────────────────────────────────────────

  useEffect(() => {
    const restoreSession = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.getMe();
        setUser(res.data);
      } catch {
        // Token expired or invalid — clean up
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    restoreSession();
  }, []);

  // ── Login ─────────────────────────────────────────────────────────────────

  /**
   * login({ identifier, password })
   *   identifier = username or email
   *   password   = plaintext password
   *
   * Calls POST /auth/token (form-encoded) then GET /users/me.
   * Persists token + full user object to localStorage.
   * Throws on error so the Login page can display an error message.
   */
  const login = useCallback(async ({ identifier, password }) => {
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', identifier);
    formData.append('password', password);

    // Step 1: Get token
    const tokenRes = await api.login(formData);
    const { access_token } = tokenRes.data;

    // Persist token immediately so next request includes it
    localStorage.setItem('token', access_token);

    // Step 2: Hydrate full user profile
    const meRes = await api.getMe();
    const fullUser = meRes.data;

    // Persist user object for quick access
    localStorage.setItem('user', JSON.stringify(fullUser));
    setUser(fullUser);

    return fullUser; // Login.jsx can read role/county to redirect
  }, []);

  // ── Logout ────────────────────────────────────────────────────────────────

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    // Hard redirect so the axios interceptor state is also reset
    window.location.replace('/login');
  }, []);


  // ── Derived Helpers ───────────────────────────────────────────────────────

  const isAuthenticated = Boolean(user);
  const role = user?.role ?? null;
  const county = user?.county ?? null;

  // ── Context Value ─────────────────────────────────────────────────────────

  const value = {
    user,
    setUser,
    loading,
    isAuthenticated,
    role,
    county,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;