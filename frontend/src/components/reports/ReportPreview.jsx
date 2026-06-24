import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function ReportPreview({ reportType, data, loading }) {
  if (loading) return <div className="text-center py-10 text-gray-500">Loading report data...</div>;
  if (data?.error) return <div className="text-red-500 text-center py-10">{data.error}</div>;
  if (!data) return <div className="text-gray-500 text-center py-10">No data. Select a report type.</div>;

  const renderContent = () => {
    switch (reportType) {
      case 'mdr_summary':
        return (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">Total Records</p><p className="text-2xl font-bold">{data.total_records || 0}</p></div>
            <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">MDR Rate</p><p className="text-2xl font-bold text-red-600">{data.mdr_rate || 0}%</p></div>
            <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">Anomalies</p><p className="text-2xl font-bold text-yellow-600">{data.anomaly_count || 0}</p></div>
            <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">Active Counties</p><p className="text-2xl font-bold text-primary-600">{data.active_counties || 0}</p></div>
          </div>
        );
      case 'anomaly_report':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">Total Predictions</p><p className="text-2xl font-bold">{data.total_predictions || 0}</p></div>
              <div className="bg-gray-50 p-4 rounded-xl text-center"><p className="text-sm text-gray-500">Anomaly Rate</p><p className="text-2xl font-bold text-yellow-600">{data.anomaly_rate?.toFixed(1) || 0}%</p></div>
            </div>
            {data.recent_anomalies?.length > 0 && (
              <div><p className="font-medium mb-2">Recent Anomalies</p><ul className="space-y-1">{data.recent_anomalies.map((a, i) => <li key={i} className="text-sm border-l-4 border-yellow-500 pl-2">{a.pathogen_code?.toUpperCase()} in {a.county} – {new Date(a.timestamp).toLocaleDateString()}</li>)}</ul></div>
            )}
          </div>
        );
      case 'sector_comparison':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={data.sectors} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                {data.sectors?.map((_, idx) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      case 'county_ranking':
        return (
          <div className="space-y-2">{data.counties?.map((c, i) => <div key={c.county} className="flex justify-between items-center p-2 bg-gray-50 rounded"><span>{i+1}. {c.county}</span><span className="font-bold text-primary-600">{c.rate}%</span></div>)}</div>
        );
      case 'pathogen_wise':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.pathogens} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="%" />
              <YAxis type="category" dataKey="name" width={80} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="resistance" fill="#3b82f6" name="Resistance (%)" />
            </BarChart>
          </ResponsiveContainer>
        );
      case 'trend':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis unit="%" />
              <Tooltip formatter={(v) => `${v}%`} />
              <Legend />
              <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} name="MDR Rate (%)" />
            </LineChart>
          </ResponsiveContainer>
        );
      default:
        return <p className="text-center">Select a report type to see preview.</p>;
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Report Preview – {reportType.replace('_', ' ').toUpperCase()}</h2>
      {renderContent()}
    </div>
  );
}