import { useState, useEffect } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import api from '../../api/client';

export default function AnalyticsSummaryCards({
  summary: propSummary = null,
  startDate = '',
  endDate = '',
  county = '',
  pathogenCode = '',
  onRefresh = null,
}) {
  const [summary, setSummary] = useState(propSummary);
  const [loading, setLoading] = useState(!propSummary);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchSummary = async (showLoading = true) => {
    if (propSummary) return;
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (county) params.append('county', county);
      if (pathogenCode) params.append('pathogen_code', pathogenCode);
      const qs = params.toString();
      const data = await api.getSummary(qs);
      setSummary(data);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error('Failed to fetch summary:', err);
      setError('Could not load summary data.');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    if (propSummary) {
      setSummary(propSummary);
      setLoading(false);
      return;
    }
    fetchSummary(true);
    const interval = setInterval(() => fetchSummary(false), 60000);
    return () => clearInterval(interval);
  }, [startDate, endDate, county, pathogenCode, propSummary]);

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      fetchSummary(true);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50 text-center">
        <p className="text-red-500">{error}</p>
        <button onClick={handleRefresh} className="mt-2 text-primary-600 underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  const cards = [
    { label: 'Total Records', value: summary?.total_records?.toLocaleString() || 0, color: 'text-gray-800' },
    { label: 'MDR Rate', value: `${summary?.mdr_rate || 0}%`, color: summary?.mdr_rate > 40 ? 'text-red-600' : 'text-green-600' },
    { label: 'Anomalies', value: summary?.anomaly_count || 0, color: 'text-yellow-600' },
    { label: 'Active Counties', value: summary?.active_counties || 0, color: 'text-primary-600' },
  ];

  return (
    <div className="relative">
      <div className="flex justify-between items-center mb-3">
        <div className="text-xs text-gray-400">
          {lastUpdated && `Last updated: ${lastUpdated}`}
        </div>
        <button
          onClick={handleRefresh}
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          title="Refresh summary"
        >
          <ArrowPathIcon className="h-4 w-4 text-gray-500" />
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50 hover:shadow-lg transition-shadow"
          >
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}