import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { ChartBarIcon, ArrowTrendingUpIcon, MapPinIcon, BellIcon } from '@heroicons/react/24/outline';
import api from '../api/client';
import CountyHeatmap from '../components/analytics/CountyHeatmap';

export default function CountyDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [pathogenData, setPathogenData] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (user.county) params.append('county', user.county);
    const qs = params.toString();

    Promise.all([
      api.getSummary(qs),
      api.getMDRTrend(6, qs),
      api.getByPathogen(10, qs),
      api.getAlerts(qs),
    ])
      .then(([summ, trend, pathogens, alerts]) => {
        setSummary(summ);
        setTrendData(trend);
        setPathogenData(pathogens);
        setRecentAlerts(alerts.slice(0, 5));
        setLoading(false);
      })
      .catch((err) => {
        console.error('CountyDashboard fetch error:', err);
        setError('Could not load data.');
        setLoading(false);
      });
  }, [user.county]);

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" /></div>;
  if (error) return <div className="text-center py-8 text-red-500">{error}</div>;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MapPinIcon className="h-6 w-6 text-primary-600" />
          County Dashboard – {user.county}
        </h1>
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
          {user.role === 'national' ? 'National' : 'County'} view
        </span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <p className="text-sm text-gray-500">Total Records</p>
          <p className="text-2xl font-bold text-gray-900">{summary?.total_records?.toLocaleString() || 0}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <p className="text-sm text-gray-500">MDR Rate</p>
          <p className="text-2xl font-bold text-red-600">{summary?.mdr_rate || 0}%</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <p className="text-sm text-gray-500">Anomalies Detected</p>
          <p className="text-2xl font-bold text-yellow-600">{summary?.anomaly_count || 0}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <p className="text-sm text-gray-500">Active County</p>
          <p className="text-2xl font-bold text-primary-600">1</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <h3 className="text-md font-semibold text-gray-800 mb-2 flex items-center gap-2">
            <ArrowTrendingUpIcon className="h-5 w-5 text-primary-600" />
            MDR Trend (6 months)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={[0, 100]} unit="%" />
              <Tooltip formatter={(v) => `${v}%`} />
              <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} name="MDR Rate (%)" dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pathogen Resistance Chart */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
          <h3 className="text-md font-semibold text-gray-800 mb-2 flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-primary-600" />
            Resistance by Pathogen
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pathogenData} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis type="category" dataKey="name" width={80} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="resistance" fill="#10b981" name="Resistance (%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* County Heatmap (filtered to this county) */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <MapPinIcon className="h-5 w-5 text-primary-600" />
          Geographic Distribution
        </h3>
        <CountyHeatmap county={user.county} />
      </div>

      {/* Recent Alerts */}
      {recentAlerts.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <h3 className="text-md font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <BellIcon className="h-5 w-5 text-yellow-500" />
            Recent Alerts in Your County
          </h3>
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="border-l-4 border-yellow-500 pl-3 py-2">
                <p className="text-sm font-medium">{alert.message}</p>
                <p className="text-xs text-gray-500">{new Date(alert.timestamp).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}