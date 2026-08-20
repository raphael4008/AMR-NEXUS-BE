import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../../api/client';

export default function AnomalyTimeline({ startDate, endDate, county }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnomalies = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (county) params.append('county', county);

        const alerts = await api.getAlerts(params.toString());

        if (!alerts || alerts.length === 0) {
          setData([]);
          setLoading(false);
          return;
        }

        const anomaliesByMonth = alerts.reduce((acc, alert) => {
          const date = new Date(alert.timestamp);
          const month = date.toLocaleString('default', { month: 'short', year: 'numeric' });
          acc[month] = (acc[month] || 0) + 1;
          return acc;
        }, {});

        const chartData = Object.entries(anomaliesByMonth)
          .map(([month, count]) => ({ month, count }))
          .sort((a, b) => {
            const dateA = new Date(a.month);
            const dateB = new Date(b.month);
            return dateA - dateB;
          });

        setData(chartData);
      } catch (err) {
        console.error('Failed to fetch anomaly timeline:', err);
        setError('Could not load anomaly timeline.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnomalies();
  }, [startDate, endDate, county]);

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-600 text-sm">Loading anomalies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 flex items-center justify-center h-64">
        <div className="text-center text-red-500">
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="mt-2 text-primary-600 underline text-sm">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 flex items-center justify-center h-64">
        <p className="text-gray-500 text-center">No anomalies detected in this period.</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold mb-2 text-gray-800">Anomaly Timeline</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <XAxis dataKey="month" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#eab308"
            fill="#fef08a"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}