export default function AlertStatsSummary({ alerts }) {
  const high = alerts.filter(a => a.severity === 'high').length;
  const medium = alerts.filter(a => a.severity === 'medium').length;
  const low = alerts.filter(a => a.severity === 'low').length;
  const acknowledged = alerts.filter(a => a.acknowledged).length;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
        <div><p className="text-xs text-gray-500">Critical</p><p className="text-lg font-bold text-red-600">{high}</p></div>
        <div><p className="text-xs text-gray-500">Warning</p><p className="text-lg font-bold text-yellow-600">{medium}</p></div>
        <div><p className="text-xs text-gray-500">Info</p><p className="text-lg font-bold text-blue-600">{low}</p></div>
        <div><p className="text-xs text-gray-500">Acknowledged</p><p className="text-lg font-bold text-green-600">{acknowledged}</p></div>
      </div>
    </div>
  );
}
