export default function HistoryStatsSummary({ data }) {
  const total = data.length;
  const mdrCount = data.filter(d => d.mdr_flag).length;
  const anomalyCount = data.filter(d => d.anomaly_detected).length;
  const uniqueCounties = [...new Set(data.map(d => d.county))].length;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
        <div>
          <p className="text-xs text-gray-500">Showing</p>
          <p className="text-lg font-bold">{total}</p>
          <p className="text-xs text-gray-400">records</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">MDR rate</p>
          <p className="text-lg font-bold text-red-600">{total ? ((mdrCount/total)*100).toFixed(1) : 0}%</p>
          <p className="text-xs text-gray-400">({mdrCount} resistant)</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Anomalies</p>
          <p className="text-lg font-bold text-yellow-600">{anomalyCount}</p>
          <p className="text-xs text-gray-400">unusual patterns</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Counties</p>
          <p className="text-lg font-bold text-primary-600">{uniqueCounties}</p>
          <p className="text-xs text-gray-400">affected</p>
        </div>
      </div>
    </div>
  );
}