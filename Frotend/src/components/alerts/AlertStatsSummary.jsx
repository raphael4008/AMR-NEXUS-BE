import { useState, useEffect } from 'react';
import api from '../../api/client';

export default function AlertStatsSummary({
  county = '',
  startDate = '',
  endDate = '',
  autoRefresh = true,
  refreshInterval = 30000,
}) {
  const [stats, setStats] = useState({ high: 0, medium: 0, low: 0, acknowledged: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (county) params.append('county', county);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const alerts = await api.getAlerts(params.toString());

      let high = 0, medium = 0, low = 0, acknowledged = 0;
      alerts.forEach(alert => {
        const severity = inferSeverity(alert.message);
        if (severity === 'high') high++;
        else if (severity === 'medium') medium++;
        else low++;
        if (alert.is_read) acknowledged++;
      });

      setStats({ high, medium, low, acknowledged, total: alerts.length });
      setError(null);
    } catch (err) {
      console.error('Failed to fetch alert stats:', err);
      setError('Could not load stats.');
    } finally {
      setLoading(false);
    }
  };

  function inferSeverity(message) {
    const msg = (message || '').toLowerCase();
    if (msg.includes('critical') || msg.includes('high') || msg.includes('spike') || msg.includes('severe')) {
      return 'high';
    }
    if (msg.includes('warning') || msg.includes('medium') || msg.includes('alert')) {
      return 'medium';
    }
    return 'low';
  }

  useEffect(() => {
    fetchStats();
    if (autoRefresh) {
      const interval = setInterval(fetchStats, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [county, startDate, endDate, autoRefresh, refreshInterval]);

  if (loading && stats.total === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto mb-1"></div>
              <div className="h-6 bg-gray-200 rounded w-3/4 mx-auto"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 text-center">
        <p className="text-red-500 text-sm">{error}</p>
        <button onClick={fetchStats} className="mt-2 text-primary-600 underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
        <div>
          <p className="text-xs text-gray-500">Critical</p>
          <p className="text-lg font-bold text-red-600">{stats.high}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Warning</p>
          <p className="text-lg font-bold text-yellow-600">{stats.medium}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Info</p>
          <p className="text-lg font-bold text-blue-600">{stats.low}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Acknowledged</p>
          <p className="text-lg font-bold text-green-600">{stats.acknowledged}</p>
        </div>
      </div>
    </div>
  );
}