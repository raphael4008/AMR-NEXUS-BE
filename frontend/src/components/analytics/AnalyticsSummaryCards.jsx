export default function AnalyticsSummaryCards({ summary }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
        <p className="text-sm text-gray-500">Total Records</p>
        <p className="text-2xl font-bold">{summary?.total_records?.toLocaleString() || 0}</p>
      </div>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
        <p className="text-sm text-gray-500">MDR Rate</p>
        <p className="text-2xl font-bold text-red-600">{summary?.mdr_rate || 0}%</p>
      </div>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
        <p className="text-sm text-gray-500">Anomalies</p>
        <p className="text-2xl font-bold text-yellow-600">{summary?.anomaly_count || 0}</p>
      </div>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md p-5 border border-white/50">
        <p className="text-sm text-gray-500">Active Counties</p>
        <p className="text-2xl font-bold text-primary-600">{summary?.active_counties || 0}</p>
      </div>
    </div>
  );
}