// src/components/dashboard/MetricsCards.jsx
import { ChartBarIcon, ArrowTrendingUpIcon, BellIcon, MapPinIcon } from '@heroicons/react/24/outline';

const getMdrColor = (rate) => {
  if (rate > 60) return 'text-red-600';
  if (rate > 30) return 'text-orange-500';
  return 'text-green-600';
};

export default function MetricsCards({ summary, anomalyCount }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-md border border-white/50">
        <div className="flex justify-between items-start">
          <p className="text-sm text-gray-500">Total Records</p>
          <ChartBarIcon className="h-5 w-5 text-gray-400" />
        </div>
        <p className="text-2xl font-bold mt-1">{summary?.total_records?.toLocaleString() || 0}</p>
        <p className="text-xs text-gray-400 mt-1">Lifetime isolates</p>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-md border border-white/50">
        <div className="flex justify-between items-start">
          <p className="text-sm text-gray-500">MDR Rate</p>
          <ArrowTrendingUpIcon className="h-5 w-5 text-gray-400" />
        </div>
        <p className={`text-2xl font-bold ${getMdrColor(summary?.mdr_rate || 0)}`}>{summary?.mdr_rate || 0}%</p>
        <p className="text-xs text-gray-400 mt-1">Multidrug‑resistant proportion</p>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-md border border-white/50">
        <div className="flex justify-between items-start">
          <p className="text-sm text-gray-500">Active Alerts</p>
          <BellIcon className="h-5 w-5 text-gray-400" />
        </div>
        <p className="text-2xl font-bold text-yellow-600">{anomalyCount}</p>
        <p className="text-xs text-gray-400 mt-1">Unusual resistance patterns</p>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-5 shadow-md border border-white/50">
        <div className="flex justify-between items-start">
          <p className="text-sm text-gray-500">Active Counties</p>
          <MapPinIcon className="h-5 w-5 text-gray-400" />
        </div>
        <p className="text-2xl font-bold text-primary-600">{summary?.active_counties || 0}</p>
        <p className="text-xs text-gray-400 mt-1">Reporting sites</p>
      </div>
    </div>
  );
}