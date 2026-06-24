import { useState, useEffect } from 'react';
import api from '../api/client';

export function useNotifications() {
  const [count, setCount] = useState(0);
  const [alerts, setAlerts] = useState([]);

  const fetchNotifications = async () => {
    try {
      // Use existing /alerts or /predictions? We'll use /alerts (you need to create it)
      // For now, fallback to anomalies from /predictions
      const predictions = await api.getPredictions(100, 0);
      const anomalies = predictions.filter(p => p.anomaly_detected);
      setCount(anomalies.length);
      setAlerts(anomalies.slice(0, 5).map(a => ({
        id: a.record_id,
        message: `${a.pathogen_code?.toUpperCase()} in ${a.county}`,
        timestamp: a.timestamp,
        severity: 'medium'
      })));
    } catch (err) {
      console.error('Notification fetch failed', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  return { count, alerts };
}