import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

const MAX_ITEMS = 5;
const STORAGE_KEY = 'recent_activity';

export function useRecentActivity() {
  const location = useLocation();
  const [activities, setActivities] = useState([]);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) setActivities(JSON.parse(stored));
  }, []);

  // Add current route to recent list when location changes
  useEffect(() => {
    const newActivity = {
      path: location.pathname,
      title: getPageTitle(location.pathname),
      timestamp: new Date().toISOString(),
    };
    setActivities(prev => {
      const filtered = prev.filter(a => a.path !== location.pathname);
      const updated = [newActivity, ...filtered].slice(0, MAX_ITEMS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, [location]);

  const clearActivities = () => {
    localStorage.removeItem(STORAGE_KEY);
    setActivities([]);
  };

  return { activities, clearActivities };
}

function getPageTitle(path) {
  const titles = {
    '/': 'Dashboard',
    '/predict': 'New Prediction',
    '/analytics': 'Analytics',
    '/history': 'History',
    '/alerts': 'Alerts',
    '/reports': 'Reports',
    '/settings': 'Settings',
    '/compare': 'Compare',
    '/pathogen-explorer': 'Pathogen Explorer',
    '/bulk-import': 'Bulk Import',
    '/compare-analytics': 'Compare Analytics',
    '/data-quality': 'Data Quality',
  };
  return titles[path] || 'AMR Nexus';
}