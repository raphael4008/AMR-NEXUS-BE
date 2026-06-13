import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

let socket;
export function useRealtimeAlerts() {
  const [alerts, setAlerts] = useState([]);
  useEffect(() => {
    // Socket.IO not available — real alerts come from GET /intelligence/alerts via polling
    // See: src/pages/Alerts.jsx for polling implementation
    socket.on('new_anomaly', (alert) => {
      setAlerts(prev => [alert, ...prev]);
      if (Notification.permission === 'granted') {
        new Notification('AMR Alert', { body: alert.message });
      }
    });
    return () => socket.disconnect();
  }, []);
  return alerts;
}
