// src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import MetricsCards from '../components/dashboard/MetricsCards';
import AnomaliesFeed from '../components/dashboard/AnomaliesFeed';
import MDRTrendMini from '../components/dashboard/MDRTrendMini';
import TopCounties from '../components/dashboard/TopCounties';
import SystemHealth from '../components/dashboard/SystemHealth';
import QuickActions from '../components/dashboard/QuickActions';
import api from '../api/client';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [trend, setTrend] = useState([]);
  const [topCounties, setTopCounties] = useState([]);
  const [health, setHealth] = useState(null);
  const [lastPrediction, setLastPrediction] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  const fetchDashboardData = async () => {
  setLoading(true);
  try {
    // 1. Fetch data with better error handling
    const [summaryData, predictions, trendData, counties, healthData] = await Promise.all([
      api.getSummary().catch(() => null),        // Returns null on failure
      api.getPredictions(100, 0).catch(() => []), // Returns empty array on failure
      api.getMDRTrend(6).catch(() => []),
      api.getTopCounties(3).catch(() => []),
      api.health().catch(() => ({ status: 'offline' })),
    ]);

    // 2. Defensive assignment (Ensuring arrays)
    setSummary(summaryData);
    
    // Safety check: Ensure predictions is an array before calling filter
    const safePredictions = Array.isArray(predictions) ? predictions : [];
    setAnomalies(safePredictions.filter(p => p.anomaly_detected).slice(0, 5));
    
    setTrend(Array.isArray(trendData) ? trendData : []);
    setTopCounties(Array.isArray(counties) ? counties : []);
    setHealth(healthData);
    
    if (safePredictions.length > 0) setLastPrediction(safePredictions[0].timestamp);
  } catch (err) {
    console.error('Dashboard data error:', err);
  } finally {
    setLoading(false);
  }
};
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">AMR‑Nexus Command Centre</h1>
        <QuickActions />
      </div>

      {/* Key metrics row */}
      <MetricsCards summary={summary} anomalyCount={anomalies.length} />

      {/* Two‑column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MDRTrendMini trend={trend} />
        <TopCounties counties={topCounties} />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AnomaliesFeed anomalies={anomalies} />
        <SystemHealth health={health} lastPrediction={lastPrediction} />
      </div>
    </div>
  );
}