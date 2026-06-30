/**
 * useRealtimeAlerts.js — AMR-Nexus Realtime Alert Hook
 *
 * The backend does not implement Socket.IO.
 * This hook polls GET /alerts every 30s and surfaces newly-arrived alerts
 * (those not seen in the previous poll) as "realtime" notifications.
 *
 * Replaces the broken: io('http://localhost:8000')
 */
import { useEffect, useState, useRef } from 'react';
import api from '../api/client';

export function useRealtimeAlerts() {
  const [alerts, setAlerts]     = useState([]);
  const seenIds                 = useRef(new Set());

  useEffect(() => {
    const poll = async () => {
      try {
        const res  = await api.getAlerts();
        const raw  = Array.isArray(res.data) ? res.data : [];
        const newAlerts = raw.filter(a => !seenIds.current.has(a.id));

        if (newAlerts.length > 0) {
          newAlerts.forEach(a => seenIds.current.add(a.id));
          // Map to the shape components expect
          const mapped = newAlerts.map(a => ({
            id:      a.id,
            message: a.summary ?? `${a.pathogen ?? 'Alert'} in ${a.county ?? '—'}`,
            county:  a.county,
          }));
          setAlerts(prev => [...mapped, ...prev].slice(0, 20));

          // Browser push notification (if permission granted)
          if (Notification.permission === 'granted') {
            mapped.forEach(a => {
              new Notification('AMR Alert', { body: a.message });
            });
          }
        }
      } catch {
        // Silently degrade
      }
    };

    // Initial fetch
    poll();
    const interval = setInterval(poll, 30_000);
    return () => clearInterval(interval);
  }, []);

  return alerts;
}
