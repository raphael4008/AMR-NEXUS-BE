import { FunnelIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function AlertFilters({ severityFilter, setSeverityFilter, typeFilter, setTypeFilter, showAcknowledged, setShowAcknowledged, onRefresh, loading }) {
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-4 w-4 text-gray-400" />
          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm">
            <option value="all">All severities</option>
            <option value="high">Critical</option>
            <option value="medium">Warning</option>
            <option value="low">Info</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-4 w-4 text-gray-400" />
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm">
            <option value="all">All types</option>
            <option value="anomaly">Anomaly</option>
            <option value="trend">Trend (high MDR)</option>
          </select>
        </div>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={showAcknowledged} onChange={(e) => setShowAcknowledged(e.target.checked)} className="rounded" />
          <span className="text-sm text-gray-600">Show acknowledged</span>
        </label>
        <button onClick={onRefresh} disabled={loading} className="flex items-center justify-center gap-2 px-4 py-2 bg-primary-50 text-primary-600 rounded-full text-sm font-medium hover:bg-primary-100 transition disabled:opacity-50">
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
}
