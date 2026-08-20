import { useState, useEffect } from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../../api/client';

export default function AcknowledgeAlertsButton({
  county = '',
  startDate = '',
  endDate = '',
  onAcknowledge = null,
  autoRefresh = true,
  refreshInterval = 30000,
}) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (county) params.append('county', county);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('unacknowledged', 'true');
      const data = await api.getAlerts(params.toString());
      setAlerts(data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch unacknowledged alerts:', err);
      setError('Could not load alerts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [county, startDate, endDate, autoRefresh, refreshInterval]);

  const handleAcknowledgeAll = async () => {
    const ids = alerts.map(a => a.id);
    if (ids.length === 0) return;
    if (!window.confirm(`Acknowledge ${ids.length} alert(s)?`)) return;

    setProcessing(true);
    try {
      await api.acknowledgeAlerts(ids);
      setAlerts([]);
      toast.success(`${ids.length} alert(s) acknowledged`);
      if (onAcknowledge) onAcknowledge(ids);
    } catch (err) {
      console.error('Failed to acknowledge alerts:', err);
      toast.error('Failed to acknowledge alerts.');
      await fetchAlerts();
    } finally {
      setProcessing(false);
    }
  };

  const unacknowledgedCount = alerts.length;

  if (loading) {
    return (
      <button
        disabled
        className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 opacity-50 cursor-not-allowed"
      >
        <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
        Loading...
      </button>
    );
  }

  if (error) {
    return (
      <button
        onClick={fetchAlerts}
        className="px-4 py-2 border border-red-300 rounded-full text-sm font-medium flex items-center gap-2 text-red-600 hover:bg-red-50 transition"
      >
        <XCircleIcon className="h-4 w-4" />
        Retry
      </button>
    );
  }

  if (unacknowledgedCount === 0) {
    return null;
  }

  return (
    <button
      onClick={handleAcknowledgeAll}
      disabled={processing}
      className={`px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition ${
        processing ? 'opacity-50 cursor-not-allowed' : ''
      }`}
    >
      {processing ? (
        <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
      ) : (
        <CheckCircleIcon className="h-4 w-4" />
      )}
      {processing ? 'Acknowledging...' : `Acknowledge All (${unacknowledgedCount})`}
    </button>
  );
}