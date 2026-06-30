import { useEffect, useState } from 'react';
import api from '../api/client';
import AlertCard from '../components/alerts/AlertCard';
import AlertFilters from '../components/alerts/AlertFilters';
import AlertStatsSummary from '../components/alerts/AlertStatsSummary';
import ExportAlertsButton from '../components/alerts/ExportAlertsButton';
import AcknowledgeAlertsButton from '../components/alerts/AcknowledgeAlertsButton';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      // Use the real /alerts endpoint instead of constructing from predictions
      const res = await api.getAlerts();
      const backendAlerts = Array.isArray(res.data) ? res.data : [];

      // Map backend Alert schema to UI Alert schema
      const newAlerts = backendAlerts.map((a) => ({
        id:           a.id ?? `alert-${Math.random()}`,
        message:      a.summary ?? `Resistance alert: ${a.pathogen} in ${a.county}`,
        timestamp:    a.triggered_at ?? new Date().toISOString(),
        severity:     a.risk_score >= 0.8 ? 'high' : a.risk_score >= 0.5 ? 'medium' : 'low',
        type:         a.anomaly_type ?? 'anomaly',
        acknowledged: a.status === 'ACKNOWLEDGED',
        details:      `${a.pathogen ?? ''} · ${a.drug_class ?? ''} · County: ${a.county ?? ''} · Score: ${a.anomaly_score?.toFixed(3) ?? 'N/A'}`,
        county:       a.county,
        pathogen:     a.pathogen,
        sector:       a.sector,
      }));

      newAlerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setAlerts(newAlerts);
    } catch (err) {
      console.error('[Alerts]', err);
      setError('Could not load alerts. Check backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = [...alerts];
    if (severityFilter !== 'all') filtered = filtered.filter(a => a.severity === severityFilter);
    if (typeFilter !== 'all') filtered = filtered.filter(a => a.type === typeFilter);
    if (!showAcknowledged) filtered = filtered.filter(a => !a.acknowledged);
    setFilteredAlerts(filtered);
  }, [alerts, severityFilter, typeFilter, showAcknowledged]);

  const handleAcknowledge = (id) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a));
  };

  const handleAcknowledgeAll = (ids) => {
    setAlerts(prev => prev.map(a => ids.includes(a.id) ? { ...a, acknowledged: true } : a));
  };

  const handleDismiss = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  if (loading) return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div></div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

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
          {filteredAlerts.map(alert => (
            <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} onDismiss={handleDismiss} />
          ))}
        </div>
      )}
    </div>
  );
}
