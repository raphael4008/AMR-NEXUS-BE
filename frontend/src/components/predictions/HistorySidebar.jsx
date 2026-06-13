import { useEffect, useState } from 'react';
import api from '../../api/client';

export default function HistorySidebar({ onSelect }) {
  const [predictions, setPredictions] = useState([]);
  useEffect(() => {
    api.getPredictions(5, 0).then(setPredictions);
  }, []);
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 mt-6">
      <h4 className="text-sm font-semibold text-gray-800 mb-2">Recent predictions</h4>
      <div className="space-y-2">
        {predictions.map(p => (
          <button key={p.record_id} onClick={() => onSelect(p)} className="w-full text-left text-xs p-2 bg-gray-50 rounded-lg hover:bg-gray-100">
            {p.pathogen_code?.toUpperCase()} in {p.county}<br/>
            <span className="text-gray-400">{new Date(p.timestamp).toLocaleDateString()}</span>
          </button>
        ))}
      </div>
    </div>
  );
}