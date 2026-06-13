export default function HistoryTable({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500 text-center py-8">No predictions yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Date</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Pathogen</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">County</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">MDR</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Probability</th>
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Anomaly</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm text-gray-800 border-b">{row.timestamp || new Date().toLocaleString()}</td>
              <td className="px-4 py-2 text-sm text-gray-800 border-b">{row.pathogen_code?.toUpperCase() || 'N/A'}</td>
              <td className="px-4 py-2 text-sm text-gray-800 border-b">{row.county || 'N/A'}</td>
              <td className="px-4 py-2 text-sm text-gray-800 border-b">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${row.mdr_flag ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {row.mdr_flag ? 'Yes' : 'No'}
                </span>
              </td>
              <td className="px-4 py-2 text-sm text-gray-800 border-b">{((row.mdr_probability || 0) * 100).toFixed(0)}%</td>
              <td className="px-4 py-2 text-sm text-gray-800 border-b">{row.anomaly_detected ? '⚠️' : '✓'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}