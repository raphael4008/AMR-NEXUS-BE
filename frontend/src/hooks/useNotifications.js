/**
 * useNotifications.js — AMR-Nexus Notification Bell Hook
 *
 * Polls GET /alerts every 60s to populate the header bell icon.
 * Uses the real /alerts endpoint (purpose-built, returns fewer, richer objects).
 * Falls back gracefully — never throws to the caller.
 */
import { useState, useEffect } from 'react';
import api from '../api/client';

export function useNotifications() {
  const [count, setCount]   = useState(0);
  const [alerts, setAlerts] = useState([]);

  const fetchNotifications = async () => {
    try {
      const res = await api.getAlerts();
      const raw = Array.isArray(res.data) ? res.data : [];
      // Only show PENDING (unacknowledged) alerts in the bell
      const pending = raw.filter(a => a.status !== 'ACKNOWLEDGED');
      setCount(pending.length);
      setAlerts(
        pending.slice(0, 5).map(a => ({
          id:        a.id,
          message:   a.summary ?? `${a.pathogen ?? 'Unknown pathogen'} in ${a.county ?? 'Unknown county'}`,
          timestamp: a.triggered_at ?? new Date().toISOString(),
          severity:  a.risk_score >= 0.8 ? 'high' : a.risk_score >= 0.5 ? 'medium' : 'low',
        }))
      );
    } catch (err) {
      // Silently degrade — bell just shows 0 if backend is unreachable
      console.warn('[useNotifications] fetch failed:', err?.response?.status ?? err?.message);
    }
  };

  useEffect(() => {
    // Initial fetch on mount
    fetchNotifications();
    // Poll every 60 seconds
    const interval = setInterval(fetchNotifications, 60_000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { count, alerts };
}