import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState({
    role: localStorage.getItem('role') || 'county',
    county: localStorage.getItem('county') || 'Nairobi',
    name: localStorage.getItem('userName') || 'John Doe',
    email: localStorage.getItem('userEmail') || 'john.doe@amrnexus.org'
  });

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('role', userData.role);
    localStorage.setItem('county', userData.county || '');
    localStorage.setItem('userName', userData.name);
    localStorage.setItem('userEmail', userData.email);
  };

  const logout = () => {
    localStorage.clear();
    setUser({ role: 'county', county: 'Nairobi', name: 'John Doe', email: '' });
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
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
