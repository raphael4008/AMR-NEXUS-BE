// src/components/dashboard/MDRTrendMini.jsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function MDRTrendMini({ trend }) {
  if (!trend || trend.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold text-gray-800 mb-2">MDR Trend (last 6 months)</h3>
        <p className="text-gray-500 text-center py-8">Not enough data</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold text-gray-800 mb-2">MDR Trend (last 6 months)</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={trend}>
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis unit="%" tick={{ fontSize: 12 }} domain={[0, 100]} />
          <Tooltip formatter={(v) => `${v}%`} />
          <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}