import { useState, useEffect } from 'react';
import api from '../api/client';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      // Replace with actual /me endpoint when ready
      // For now, read from localStorage or mock
      const stored = localStorage.getItem('user');
      if (stored) {
        setUser(JSON.parse(stored));
      } else {
        // Mock user – replace with API call
        setUser({ name: 'John Doe', email: 'john.doe@amrnexus.org', role: 'epidemiologist' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('user');
    setUser(null);
    // Call backend logout endpoint if needed
    window.location.href = '/login';
  };

  useEffect(() => {
    fetchUser();
  }, []);

  return { user, loading, logout };
}