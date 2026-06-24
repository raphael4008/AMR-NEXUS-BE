import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

let socket;
export function useRealtimeAlerts() {
  const [alerts, setAlerts] = useState([]);
  useEffect(() => {
    socket = io('http://localhost:8000');
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
