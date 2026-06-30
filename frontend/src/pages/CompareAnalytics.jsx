import { useState } from 'react';
import api from '../api/client';

export default function CompareAnalytics() {
  const [period1, setPeriod1] = useState({ start: '2024-01-01', end: '2024-06-30' });
  const [period2, setPeriod2] = useState({ start: '2024-07-01', end: '2024-12-31' });
  const [data1, setData1] = useState(null);
  const [data2, setData2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res1, res2] = await Promise.all([
        api.getSummary({ start_date: period1.start, end_date: period1.end }),
        api.getSummary({ start_date: period2.start, end_date: period2.end }),
      ]);
      setData1(res1.data ?? null);
      setData2(res2.data ?? null);
    } catch (err) {
      console.error('[CompareAnalytics]', err);
      setError('Failed to load comparison data. Check backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Comparative Analytics</h1>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period 1</label>
            <div className="flex gap-2">
              <input type="date" value={period1.start} onChange={e => setPeriod1({ ...period1, start: e.target.value })} className="flex-1 rounded-full border border-gray-300 p-2 text-sm" />
              <input type="date" value={period1.end}   onChange={e => setPeriod1({ ...period1, end:   e.target.value })} className="flex-1 rounded-full border border-gray-300 p-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period 2</label>
            <div className="flex gap-2">
              <input type="date" value={period2.start} onChange={e => setPeriod2({ ...period2, start: e.target.value })} className="flex-1 rounded-full border border-gray-300 p-2 text-sm" />
              <input type="date" value={period2.end}   onChange={e => setPeriod2({ ...period2, end:   e.target.value })} className="flex-1 rounded-full border border-gray-300 p-2 text-sm" />
            </div>
          </div>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="px-4 py-2 bg-primary-600 text-white rounded-full text-sm hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Loading…' : 'Compare Periods'}
        </button>
      </div>

      {error && <div className="text-center text-red-500 text-sm p-4">{error}</div>}

      {data1 && data2 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[{ label: 'Period 1', d: data1, range: period1 }, { label: 'Period 2', d: data2, range: period2 }].map(({ label, d, range }) => (
            <div key={label} className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-3">
              <h3 className="font-semibold text-gray-800">{label}</h3>
              <p className="text-xs text-gray-400">{range.start} → {range.end}</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-600">Total Records</span><span className="font-bold">{d.total_records?.toLocaleString() ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">MDR Rate</span><span className="font-bold text-red-600">{d.mdr_rate != null ? `${d.mdr_rate.toFixed(1)}%` : '—'}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Anomalies</span><span className="font-bold text-amber-600">{d.anomaly_count ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Active Counties</span><span className="font-bold">{d.active_counties ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Compliance Index</span><span className="font-bold text-green-600">{d.compliance_index != null ? `${(d.compliance_index * 100).toFixed(1)}%` : '—'}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {data1 && data2 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <h3 className="font-semibold text-gray-800 mb-3">Delta (Period 2 − Period 1)</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {[
              { label: 'Records Δ', val: (data2.total_records ?? 0) - (data1.total_records ?? 0) },
              { label: 'MDR Rate Δ', val: data1.mdr_rate != null && data2.mdr_rate != null ? parseFloat((data2.mdr_rate - data1.mdr_rate).toFixed(2)) : null, unit: 'pp' },
              { label: 'Anomalies Δ', val: (data2.anomaly_count ?? 0) - (data1.anomaly_count ?? 0) },
              { label: 'Counties Δ', val: (data2.active_counties ?? 0) - (data1.active_counties ?? 0) },
            ].map(({ label, val, unit = '' }) => (
              <div key={label} className="rounded-xl bg-gray-50 border p-3">
                <p className="text-gray-500 text-xs">{label}</p>
                <p className={`text-xl font-bold ${val > 0 ? 'text-red-500' : val < 0 ? 'text-green-600' : 'text-gray-700'}`}>
                  {val != null ? `${val > 0 ? '+' : ''}${val}${unit}` : '—'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
