// src/pages/Alerts.jsx
import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import toast, { Toaster } from 'react-hot-toast';
import api from '../api/client';
import AlertCard from '../components/alerts/AlertCard';
import AlertFilters from '../components/alerts/AlertFilters';
import AlertStatsSummary from '../components/alerts/AlertStatsSummary';
import ExportAlertsButton from '../components/alerts/ExportAlertsButton';
import AcknowledgeAlertsButton from '../components/alerts/AcknowledgeAlertsButton';

export default function Alerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const [expandedAlertId, setExpandedAlertId] = useState(null);
  const [guidanceMap, setGuidanceMap] = useState({});

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (user?.county) params.append('county', user.county);
      const qs = params.toString();

      // Fetch from new /alerts endpoint
      const data = await api.getAlerts(qs);
      setAlerts(data);
    } catch (err) {
      console.error('Alerts fetch error:', err);
      setError('Could not load alerts.');
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, [user?.county]);

  // Apply filters
  useEffect(() => {
    let filtered = [...alerts];
    if (severityFilter !== 'all') {
      filtered = filtered.filter(a => a.severity === severityFilter);
    }
    if (typeFilter !== 'all') {
      filtered = filtered.filter(a => a.type === typeFilter);
    }
    if (!showAcknowledged) {
      filtered = filtered.filter(a => !a.acknowledged);
    }
    setFilteredAlerts(filtered);
  }, [alerts, severityFilter, typeFilter, showAcknowledged]);

  const handleAcknowledge = (id) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a));
    toast.success('Alert acknowledged');
  };

  const handleAcknowledgeAll = (ids) => {
    setAlerts(prev => prev.map(a => ids.includes(a.id) ? { ...a, acknowledged: true } : a));
    toast.success(`${ids.length} alert(s) acknowledged`);
  };

  const handleDismiss = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const fetchGuidance = async (alert) => {
    if (guidanceMap[alert.id]) return;
    try {
      const response = await fetch('http://localhost:8000/guidance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pathogen_code: alert.pathogen_code,
          resistance_pattern: alert.resistance_pattern || 'ESBL',
          user_role: user?.role || 'county',
          county: user?.county || 'Nairobi',
        }),
      });
      const data = await response.json();
      setGuidanceMap(prev => ({ ...prev, [alert.id]: data.guidance }));
    } catch (err) {
      console.error('Guidance fetch error:', err);
      toast.error('Could not load guidance');
    }
  };

  const toggleGuidance = (alert) => {
    const id = alert.id;
    if (expandedAlertId === id) {
      setExpandedAlertId(null);
    } else {
      setExpandedAlertId(id);
      if (!guidanceMap[id]) {
        fetchGuidance(alert);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return <div className="text-center text-red-500 p-8">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />
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
            <div key={alert.id}>
              <AlertCard
                alert={alert}
                onAcknowledge={handleAcknowledge}
                onDismiss={handleDismiss}
                onToggleGuidance={() => toggleGuidance(alert)}
                isExpanded={expandedAlertId === alert.id}
                guidance={guidanceMap[alert.id] || null}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}