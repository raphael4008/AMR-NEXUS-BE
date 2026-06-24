// src/components/dashboard/AnomaliesFeed.jsx
import { useState } from 'react';
import { BellAlertIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export default function AnomaliesFeed({ anomalies }) {
  const [dismissed, setDismissed] = useState([]);
  const activeAnomalies = anomalies.filter(a => !dismissed.includes(a.record_id));

  const dismissAnomaly = (id) => {
    setDismissed([...dismissed, id]);
    // Optionally call an API to record dismissal (not implemented here)
  };

  if (activeAnomalies.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircleIcon className="h-5 w-5 text-green-500" />
          <h3 className="text-md font-semibold text-gray-800">Recent Anomalies</h3>
        </div>
        <p className="text-gray-500 text-center py-4">No active anomalies. System is stable.</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="flex items-center gap-2 mb-3">
        <BellAlertIcon className="h-5 w-5 text-yellow-500" />
        <h3 className="text-md font-semibold text-gray-800">Recent Anomalies ({activeAnomalies.length})</h3>
      </div>
      <div className="space-y-3">
        {activeAnomalies.map((anomaly) => (
          <div key={anomaly.record_id} className="border-l-4 border-yellow-500 pl-3 py-2 bg-gray-50/50 rounded-r-lg">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {anomaly.pathogen_code?.toUpperCase()} in {anomaly.county}
                </p>
                <p className="text-xs text-gray-500">{new Date(anomaly.timestamp).toLocaleString()}</p>
              </div>
              <button
                onClick={() => dismissAnomaly(anomaly.record_id)}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 text-right">
        <a href="/alerts" className="text-xs text-primary-600 hover:underline">View all →</a>
      </div>
    </div>
  );
}