import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../../api/client';

export default function AnomalyTimeline({ startDate, endDate, county }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchAnomalies = async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (county) params.append('county', county);
      const predictions = await api.getPredictions(1000, 0, params.toString());
      const anomaliesByMonth = predictions.filter(p => p.anomaly_detected).reduce((acc, p) => {
        const month = new Date(p.timestamp).toLocaleString('default', { month: 'short' });
        acc[month] = (acc[month] || 0) + 1;
        return acc;
      }, {});
      const chartData = Object.entries(anomaliesByMonth).map(([month, count]) => ({ month, count }));
      setData(chartData);
    };
    fetchAnomalies();
  }, [startDate, endDate, county]);

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold mb-2 text-gray-800">Anomaly Timeline</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="count" stroke="#eab308" fill="#fef08a" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}