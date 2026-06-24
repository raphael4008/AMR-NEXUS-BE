import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function AlertCard({ alert, onAcknowledge, onDismiss }) {
  const severityColors = {
    high: 'border-l-red-500 bg-red-50/50',
    medium: 'border-l-yellow-500 bg-yellow-50/50',
    low: 'border-l-blue-500 bg-blue-50/50',
  };
  const severityBadge = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-blue-100 text-blue-800',
  };
  const isAcknowledged = alert.acknowledged || false;

  return (
    <div className={`bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border-l-4 overflow-hidden transition-all ${severityColors[alert.severity] || severityColors.medium} ${isAcknowledged ? 'opacity-60' : ''}`}>
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${severityBadge[alert.severity]}`}>
                {alert.severity === 'high' ? 'Critical' : alert.severity === 'medium' ? 'Warning' : 'Info'}
              </span>
              <span className="text-xs text-gray-400">{new Date(alert.timestamp).toLocaleString()}</span>
              {isAcknowledged && <span className="text-xs text-green-600 flex items-center gap-1"><CheckCircleIcon className="h-3 w-3" /> Acknowledged</span>}
            </div>
            <p className="text-gray-800 font-medium">{alert.message}</p>
            {alert.details && <p className="text-sm text-gray-500 mt-1">{alert.details}</p>}
          </div>
          <div className="flex gap-2 ml-4">
            {!isAcknowledged && (
              <button onClick={() => onAcknowledge(alert.id)} className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full hover:bg-primary-200">
                Acknowledge
              </button>
            )}
            <button onClick={() => onDismiss(alert.id)} className="text-gray-400 hover:text-gray-600" title="Dismiss">
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
