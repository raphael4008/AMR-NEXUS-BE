// src/components/dashboard/SystemHealth.jsx
import { ServerIcon, CubeIcon, ClockIcon } from '@heroicons/react/24/outline';

export default function SystemHealth({ health, lastPrediction }) {  // ✅ default export
  const isOnline = health && health.status === 'ok';
  const lastPredictionDate = lastPrediction ? new Date(lastPrediction).toLocaleString() : 'Never';

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold text-gray-800 mb-3">System Health</h3>
      <div className="space-y-2">
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <ServerIcon className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">Backend API</span>
          </div>
          <span className={`text-sm font-medium ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <CubeIcon className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">ML Model</span>
          </div>
          <span className="text-sm font-medium text-gray-700">{health?.service || 'XGBoost v1.0'}</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2">
            <ClockIcon className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">Last Prediction</span>
          </div>
          <span className="text-xs text-gray-500">{lastPredictionDate}</span>
        </div>
      </div>
    </div>
  );
}