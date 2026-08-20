// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user from backend on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUserFromBackend(token);
    } else {
      // Fallback to localStorage role/county (demo mode)
      const savedRole = localStorage.getItem('role') || 'county';
      const savedCounty = localStorage.getItem('county') || 'Nairobi';
      setUser({
        role: savedRole,
        county: savedCounty,
        name: localStorage.getItem('userName') || 'John Doe',
        email: localStorage.getItem('userEmail') || 'john.doe@amrnexus.org',
      });
      setLoading(false);
    }
  }, []);

  const fetchUserFromBackend = async (token) => {
    try {
      const response = await fetch('http://localhost:8000/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch user');
      const data = await response.json();
      // Merge with backend data; keep existing fallback values
      setUser({
        role: data.role || 'county',
        county: data.county || 'Nairobi',
        name: data.name || 'John Doe',
        email: data.email || 'john.doe@amrnexus.org',
      });
    } catch (err) {
      console.error('Auth fetch error:', err);
      setError(err.message);
      // Fallback to localStorage
      const savedRole = localStorage.getItem('role') || 'county';
      const savedCounty = localStorage.getItem('county') || 'Nairobi';
      setUser({
        role: savedRole,
        county: savedCounty,
        name: localStorage.getItem('userName') || 'John Doe',
        email: localStorage.getItem('userEmail') || 'john.doe@amrnexus.org',
      });
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      // Replace with actual login endpoint
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      const { token, user: userData } = data;
      localStorage.setItem('token', token);
      setUser({
        role: userData.role || 'county',
        county: userData.county || 'Nairobi',
        name: userData.name || 'John Doe',
        email: userData.email || 'john.doe@amrnexus.org',
      });
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    window.location.href = '/login';
  };

  // For demo, if no token, allow setting role manually
  const setRoleAndCounty = (role, county) => {
    localStorage.setItem('role', role);
    localStorage.setItem('county', county);
    setUser(prev => ({ ...prev, role, county }));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        login,
        logout,
        setRoleAndCounty, // for demo purposes
        isAuthenticated: !!user,
        isNational: user?.role === 'national',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};