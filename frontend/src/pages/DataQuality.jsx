import { useEffect, useState } from 'react';
import api from '../api/client';

export default function DataQuality() {
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDataQuality()
      .then(setQuality)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
    </div>
  );
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  const score = Math.round((quality?.quality_score ?? 0) * 100);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Data Quality</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border p-6 text-center">
          <p className="text-gray-500 text-sm mb-1">Compliance Index</p>
          <p className="text-4xl font-bold text-primary-600">{score}%</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border p-6 text-center">
          <p className="text-gray-500 text-sm mb-1">Total Records</p>
          <p className="text-4xl font-bold text-gray-800">{quality?.total_records?.toLocaleString() ?? '-'}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border p-6 text-center">
          <p className="text-gray-500 text-sm mb-1">Clean Records</p>
          <p className="text-4xl font-bold text-green-600">{quality?.clean_records?.toLocaleString() ?? '-'}</p>
        </div>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border p-6">
        <h2 className="text-lg font-semibold mb-4">Compliance Progress</h2>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="h-4 rounded-full transition-all duration-700"
            style={{
              width: `${score}%`,
              background: score >= 80 ? '#16a34a' : score >= 60 ? '#d97706' : '#dc2626'
            }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-2">
          WHO GAP-AMR target: 80% national compliance index
        </p>
      </div>
    </div>
  );
}
