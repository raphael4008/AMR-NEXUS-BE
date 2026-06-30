/**
 * AnomalyTimeline.jsx — AMR-Nexus Anomaly Frequency Chart
 *
 * Fixes:
 *  1. params was URLSearchParams string passed to getPredictions() — now plain object
 *  2. anomaly_detected field name fixed (backend serialises as 'anomaly_detected')
 *  3. Month ordering fixed (sorts by calendar month, not locale string alphabetically)
 *  4. Added loading + empty states to prevent blank chart
 *  5. Light theme styling (was unstyled)
 */
import { useEffect, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts';
import api from '../../api/client';

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

export default function AnomalyTimeline({ startDate, endDate, county }) {
  const [data,    setData]    = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnomalies = async () => {
      setLoading(true);
      try {
        // FIX: pass plain object not URLSearchParams.toString()
        const params = {};
        if (startDate) params.start_date = startDate;
        if (endDate)   params.end_date   = endDate;
        if (county)    params.county     = county;

        const res  = await api.getPredictions(2000, 0, params);
        const rows = Array.isArray(res.data) ? res.data : [];

        // Group by calendar month number → label
        const monthCounts = {};
        rows.forEach(p => {
          // FIX: correct field name is 'anomaly_detected'
          if (!p.anomaly_detected) return;
          const ts = p.timestamp ?? p.sample_collection_date;
          if (!ts) return;
          const mo = new Date(ts).getMonth(); // 0-based
          monthCounts[mo] = (monthCounts[mo] || 0) + 1;
        });

        // Build sorted chart data (Jan→Dec order)
        const chartData = Object.entries(monthCounts)
          .sort(([a], [b]) => Number(a) - Number(b))
          .map(([mo, count]) => ({ month: MONTH_LABELS[Number(mo)], count }));

        setData(chartData);
      } catch (err) {
        console.error('[AnomalyTimeline]', err);
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchAnomalies();
  }, [startDate, endDate, county]);

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold mb-2 text-gray-800">Anomaly Timeline</h3>
      {loading ? (
        <div className="animate-pulse bg-gray-100 rounded-xl h-48 w-full" />
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center text-gray-400 text-sm h-48">
          No anomaly records in selected range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6b7280' }} />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }}
              formatter={v => [v, 'Anomalies']}
            />
            <Area
              type="monotone"
              dataKey="count"
              name="Anomalies"
              stroke="#f59e0b"
              fill="#fef3c7"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}