// src/components/dashboard/SystemHealth.jsx
import { ServerIcon, CubeIcon, ClockIcon, CircleStackIcon, SignalIcon } from '@heroicons/react/24/outline';

export default function SystemHealth({ health, lastPrediction }) {
  // Backend /health returns { status: "healthy", version: "x.x.x" }
  const isOnline = health && (health.status === 'ok' || health.status === 'healthy');
  const lastPredictionDate = lastPrediction ? new Date(lastPrediction).toLocaleString() : 'No data yet';

  const statusDot = (online) => (
    <span className={`inline-block w-2 h-2 rounded-full ${online ? 'bg-green-500' : 'bg-red-500'} mr-1`} />
  );

  const rows = [
    {
      icon: ServerIcon,
      label: 'Backend API',
      value: (
        <span className={`text-sm font-medium flex items-center ${isOnline ? 'text-green-600' : 'text-red-500'}`}>
          {statusDot(isOnline)}{isOnline ? 'Online' : 'Offline'}
        </span>
      ),
    },
    {
      icon: SignalIcon,
      label: 'API Version',
      value: <span className="text-sm text-gray-700">{health?.version ?? '—'}</span>,
    },
    {
      icon: CubeIcon,
      label: 'ML Model',
      value: <span className="text-sm text-gray-700">{health?.service ?? 'XGBoost v1.0'}</span>,
    },
    {
      icon: CircleStackIcon,
      label: 'Database',
      value: (
        <span className={`text-sm font-medium flex items-center ${isOnline ? 'text-green-600' : 'text-red-500'}`}>
          {statusDot(isOnline)}{isOnline ? 'Connected' : 'Unreachable'}
        </span>
      ),
    },
    {
      icon: ClockIcon,
      label: 'Last Record',
      value: <span className="text-xs text-gray-500">{lastPredictionDate}</span>,
    },
  ];

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-md font-semibold text-gray-800">System Health</h3>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
          isOnline ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {isOnline ? 'All Systems Operational' : 'Service Degraded'}
        </span>
      </div>
      <div className="space-y-0">
        {rows.map(({ icon: Icon, label, value }, i) => (
          <div
            key={label}
            className={`flex items-center justify-between py-2 ${i < rows.length - 1 ? 'border-b border-gray-100' : ''}`}
          >
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">{label}</span>
            </div>
            {value}
          </div>
        ))}
      </div>
    </div>
  );
}