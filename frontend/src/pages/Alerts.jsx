import { useEffect, useState, useCallback } from 'react';
import api from '../api/client';
import AlertCard from '../components/alerts/AlertCard';
import AlertFilters from '../components/alerts/AlertFilters';
import AlertStatsSummary from '../components/alerts/AlertStatsSummary';
import ExportAlertsButton from '../components/alerts/ExportAlertsButton';
import AcknowledgeAlertsButton from '../components/alerts/AcknowledgeAlertsButton';

export default function Alerts() {
  const [alerts, setAlerts]                   = useState([]);
  const [filteredAlerts, setFilteredAlerts]   = useState([]);
  const [loading, setLoading]                 = useState(true);
  const [error, setError]                     = useState(null);
  const [severityFilter, setSeverityFilter]   = useState('all');
  const [typeFilter, setTypeFilter]           = useState('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rawAlerts = await api.getAlerts();
      const mapped = rawAlerts.map((a) => ({
        id:           a.id,
        message:      `${a.pathogen} - ${a.drug_class} resistance in ${a.county}`,
        timestamp:    a.triggered_at ?? new Date().toISOString(),
        severity:     a.risk_score >= 70 ? 'high' : a.risk_score >= 40 ? 'medium' : 'low',
        type:         a.anomaly_type ?? 'trend',
        sector:       a.sector,
        county:       a.county,
        sub_county:   a.sub_county,
        risk_score:   a.risk_score,
        status:       a.status,
        summary:      a.summary,
        details:      a.summary,
        acknowledged: false,
      }));
      setAlerts(mapped);
    } catch (err) {
      setError('Could not load alerts: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  useEffect(() => {
    let filtered = [...alerts];
    if (severityFilter !== 'all') filtered = filtered.filter((a) => a.severity === severityFilter);
    if (typeFilter !== 'all')     filtered = filtered.filter((a) => a.type === typeFilter);
    if (!showAcknowledged)        filtered = filtered.filter((a) => !a.acknowledged);
    setFilteredAlerts(filtered);
  }, [alerts, severityFilter, typeFilter, showAcknowledged]);

  const handleAcknowledge    = (id)  => setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, acknowledged: true } : a));
  const handleAcknowledgeAll = (ids) => setAlerts((prev) => prev.map((a) => ids.includes(a.id) ? { ...a, acknowledged: true } : a));
  const handleDismiss        = (id)  => setAlerts((prev) => prev.filter((a) => a.id !== id));

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
    </div>
  );

  if (error) return (
    <div className="text-center text-red-500 p-8">
      <p>{error}</p>
      <button onClick={fetchAlerts} className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-full text-sm">Retry</button>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Stewardship Alerts</h1>
        <div className="flex gap-2">
          <ExportAlertsButton alerts={filteredAlerts} />
          <AcknowledgeAlertsButton alerts={filteredAlerts} onAcknowledgeAll={handleAcknowledgeAll} />
        </div>
      </div>
      <AlertFilters
        severityFilter={severityFilter}
        setSeverityFilter={setSeverityFilter}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        showAcknowledged={showAcknowledged}
        setShowAcknowledged={setShowAcknowledged}
        onRefresh={fetchAlerts}
        loading={loading}
      />
      <AlertStatsSummary alerts={filteredAlerts} />
      {filteredAlerts.length === 0 ? (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-8 text-center">
          <p className="text-gray-500">No alerts match your filters.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} onDismiss={handleDismiss} />
          ))}
        </div>
      )}
    </div>
  );
}
