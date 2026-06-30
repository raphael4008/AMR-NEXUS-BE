import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import api from '../api/client';
import CountyHeatmap from '../components/analytics/CountyHeatmap';
import { saveAs } from 'file-saver';

export default function PathogenExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [pathogens, setPathogens] = useState([]);
  const [selected, setSelected] = useState(searchParams.get('pathogen') || '');
  const [startDate, setStartDate] = useState(searchParams.get('start') || '');
  const [endDate, setEndDate] = useState(searchParams.get('end') || '');
  const [county, setCounty] = useState(searchParams.get('county') || '');
  const [counties, setCounties] = useState([]);
  const [resistanceData, setResistanceData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Update URL when filters change
  useEffect(() => {
    const params = {};
    if (selected) params.pathogen = selected;
    if (startDate) params.start = startDate;
    if (endDate) params.end = endDate;
    if (county) params.county = county;
    setSearchParams(params, { replace: true });
  }, [selected, startDate, endDate, county, setSearchParams]);

  // Load pathogens list and county list on mount
  useEffect(() => {
    // getByPathogen returns { status, data: [{pathogen_name, count}] }
    api.getByPathogen(100)
      .then(res => {
        const raw = Array.isArray(res.data?.data) ? res.data.data : Array.isArray(res.data) ? res.data : [];
        setPathogens(raw.map(p => p.pathogen_name ?? p.name ?? '').filter(Boolean));
      })
      .catch(() => {});
    // getTopCounties returns normalized [{county, rate, alert_count}]
    api.getTopCounties(100)
      .then(res => {
        const raw = Array.isArray(res.data) ? res.data : [];
        setCounties(raw.map(c => c.county).filter(Boolean));
      })
      .catch(() => {});
  }, []);

  // Fetch data when selected pathogen changes
  useEffect(() => {
    if (!selected) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = {};
        if (startDate) params.start_date = startDate;
        if (endDate)   params.end_date   = endDate;
        if (county)    params.county     = county;

        // Fetch all records for this pathogen and derive resistance by antibiotic class
        const res = await api.getPredictions(1000, 0, { ...params, pathogen_name: selected });
        const records = Array.isArray(res.data) ? res.data : [];

        // Resistance by antibiotic class
        const classMap = {};
        records.forEach(r => {
          const cls = r.antibiotic_class ?? r.antibiotic_name ?? 'Unknown';
          if (!classMap[cls]) classMap[cls] = { total: 0, resistant: 0 };
          classMap[cls].total++;
          if (r.mdr_flag || r.sir_result === 'R') classMap[cls].resistant++;
        });
        const resistanceArr = Object.entries(classMap).map(([cls, v]) => ({
          antibiotic_class: cls,
          resistance: v.total > 0 ? parseFloat((v.resistant / v.total * 100).toFixed(1)) : 0,
        })).sort((a, b) => b.resistance - a.resistance);
        setResistanceData(resistanceArr);

        // MDR trend — group by month
        const monthMap = {};
        records.forEach(r => {
          const month = (r.timestamp ?? '').slice(0, 7);
          if (!month) return;
          if (!monthMap[month]) monthMap[month] = { total: 0, resistant: 0 };
          monthMap[month].total++;
          if (r.mdr_flag || r.sir_result === 'R') monthMap[month].resistant++;
        });
        const trend = Object.entries(monthMap)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([month, v]) => ({
            month,
            rate: v.total > 0 ? parseFloat((v.resistant / v.total * 100).toFixed(1)) : 0,
          }));
        setTrendData(trend);
      } catch (err) {
        console.error('[PathogenExplorer]', err);
        setResistanceData([]);
        setTrendData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selected, startDate, endDate, county]);

  // Export resistance data as CSV
  const exportCSV = () => {
    if (!resistanceData.length) return;
    const headers = ['Antibiotic Class', 'Resistance (%)'];
    const rows = resistanceData.map(r => [r.antibiotic_class, r.resistance]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `${selected}_resistance_${new Date().toISOString().slice(0,19)}.csv`);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Pathogen Explorer</h1>
        <div className="flex gap-2">
          <button onClick={exportCSV} disabled={!resistanceData.length} className="px-4 py-2 bg-primary-600 text-white rounded-full text-sm">📥 Export CSV</button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-md border">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm mb-1">Pathogen</label>
            <select value={selected} onChange={e => setSelected(e.target.value)} className="w-full rounded-full border p-2">
              <option value="">Select pathogen</option>
              {pathogens.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Start Date</label>
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="w-full rounded-full border p-2" />
          </div>
          <div>
            <label className="block text-sm mb-1">End Date</label>
            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="w-full rounded-full border p-2" />
          </div>
          <div>
            <label className="block text-sm mb-1">County</label>
            <select value={county} onChange={e => setCounty(e.target.value)} className="w-full rounded-full border p-2">
              <option value="">All counties</option>
              {counties.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      {!selected && <div className="text-center p-8 text-gray-500">Select a pathogen to explore resistance patterns.</div>}

      {selected && loading && <div className="text-center p-8">Loading data...</div>}

      {selected && !loading && (
        <div className="space-y-6">
          {/* Resistance by Antibiotic Class */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border">
            <h2 className="text-lg font-semibold mb-2">Resistance by Antibiotic Class – {selected.toUpperCase()}</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={resistanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="antibiotic_class" angle={-45} textAnchor="end" height={80} />
                <YAxis unit="%" domain={[0, 100]} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="resistance" fill="#8884d8" name="MDR (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Resistance Trend */}
          {trendData.length > 0 && (
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border">
              <h2 className="text-lg font-semibold mb-2">MDR Trend (last 12 months) – {selected.toUpperCase()}</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} name="MDR Rate (%)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* County Heatmap for this pathogen */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border">
            <h2 className="text-lg font-semibold mb-2">Geographic Distribution – {selected.toUpperCase()}</h2>
            <CountyHeatmap startDate={startDate} endDate={endDate} pathogenCode={selected} />
          </div>
        </div>
      )}
    </div>
  );
}
