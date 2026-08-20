import { useEffect, useState } from 'react';
import { ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function DataQuality() {
  const [quality, setQuality] = useState(null);
  useEffect(() => {
    fetch('http://localhost:8000/analytics/data_quality').then(r=>r.json()).then(setQuality);
  }, []);
  if (!quality) return <div>Loading...</div>;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Data Quality Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/80 p-5 rounded-2xl"><p className="text-gray-500">Total Records</p><p className="text-2xl font-bold">{quality.total_records}</p></div>
        <div className="bg-white/80 p-5 rounded-2xl"><p className="text-gray-500">Missing Pathogen</p><p className="text-2xl text-yellow-600">{quality.missing_pathogen}</p></div>
        <div className="bg-white/80 p-5 rounded-2xl"><p className="text-gray-500">Missing County</p><p className="text-2xl text-yellow-600">{quality.missing_county}</p></div>
      </div>
      <div className="bg-white/80 p-5 rounded-2xl"><p>Completeness: {quality.completeness_percent}%</p><div className="w-full bg-gray-200 rounded-full h-2"><div className="bg-green-500 h-2 rounded-full" style={{width:`${quality.completeness_percent}%`}}></div></div></div>
    </div>
  );
}
