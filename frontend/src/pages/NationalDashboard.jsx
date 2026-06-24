import { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/client';
import CountyHeatmap from '../components/analytics/CountyHeatmap';

export default function NationalDashboard() {
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [topPathogens, setTopPathogens] = useState([]);

  useEffect(() => {
    Promise.all([
      api.getSummary(),
      api.getMDRTrend(6),
      api.getByPathogen(10)
    ]).then(([summ, trend, pathogens]) => {
      setSummary(summ);
      setTrend(trend);
      setTopPathogens(pathogens);
    });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">National AMR Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/80 p-4 rounded-2xl"><p className="text-sm text-gray-500">Total Records</p><p className="text-2xl font-bold">{summary?.total_records || 0}</p></div>
        <div className="bg-white/80 p-4 rounded-2xl"><p className="text-sm text-gray-500">MDR Rate</p><p className="text-2xl font-bold text-red-600">{summary?.mdr_rate || 0}%</p></div>
        <div className="bg-white/80 p-4 rounded-2xl"><p className="text-sm text-gray-500">Anomalies</p><p className="text-2xl font-bold text-yellow-600">{summary?.anomaly_count || 0}</p></div>
        <div className="bg-white/80 p-4 rounded-2xl"><p className="text-sm text-gray-500">Active Counties</p><p className="text-2xl font-bold text-primary-600">{summary?.active_counties || 0}</p></div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/80 p-5 rounded-2xl">
          <h3 className="text-lg font-semibold mb-2">National MDR Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}><XAxis dataKey="month" /><YAxis domain={[0,100]} unit="%" /><Tooltip formatter={(v) => `${v}%`} /><Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} /></LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white/80 p-5 rounded-2xl">
          <h3 className="text-lg font-semibold mb-2">Top Pathogens</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topPathogens} layout="vertical"><XAxis type="number" unit="%" /><YAxis type="category" dataKey="name" width={60} /><Tooltip formatter={(v) => `${v}%`} /><Bar dataKey="resistance" fill="#10b981" /></BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <CountyHeatmap />
    </div>
  );
}
