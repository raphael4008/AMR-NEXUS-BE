import { useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/client';

export default function CompareAnalytics() {
  const [period1, setPeriod1] = useState({ start: '2024-01-01', end: '2024-06-30' });
  const [period2, setPeriod2] = useState({ start: '2024-07-01', end: '2024-12-31' });
  const [data1, setData1] = useState(null);
  const [data2, setData2] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
        const [d1, d2] = await Promise.all([
      api.getSummary(`start_date=${period1.start}&end_date=${period1.end}`),
      api.getSummary(`start_date=${period2.start}&end_date=${period2.end}`)
    ]);
    setData1(d1); setData2(d2);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Comparative Analytics</h1>
      <div className="grid grid-cols-2 gap-4">
        <div><label>Period 1</label><input type="date" value={period1.start} onChange={e=>setPeriod1({...period1,start:e.target.value})} /><input type="date" value={period1.end} onChange={e=>setPeriod1({...period1,end:e.target.value})} /></div>
        <div><label>Period 2</label><input type="date" value={period2.start} onChange={e=>setPeriod2({...period2,start:e.target.value})} /><input type="date" value={period2.end} onChange={e=>setPeriod2({...period2,end:e.target.value})} /></div>
      </div>
      <button onClick={fetchData} className="px-4 py-2 bg-primary-600 text-white rounded-full">Compare</button>
      {loading && <div>Loading...</div>}
      {data1 && data2 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-xl"><h3>Period 1</h3><p>Total: {data1.total_records}</p><p>MDR rate: {data1.mdr_rate}%</p><p>Anomalies: {data1.anomaly_count}</p></div>
          <div className="bg-white p-4 rounded-xl"><h3>Period 2</h3><p>Total: {data2.total_records}</p><p>MDR rate: {data2.mdr_rate}%</p><p>Anomalies: {data2.anomaly_count}</p></div>
        </div>
      )}
    </div>
  );
}
