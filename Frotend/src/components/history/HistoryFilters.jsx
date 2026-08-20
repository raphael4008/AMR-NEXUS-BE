import { MagnifyingGlassIcon, FunnelIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function HistoryFilters({
  searchTerm,
  setSearchTerm,
  filterMDR,
  setFilterMDR,
  filterAnomaly,
  setFilterAnomaly,
  onRefresh,
  loading,
}) {
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search pathogen or county..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-full border border-gray-200 bg-gray-50/50 focus:ring-2 focus:ring-primary-500/20"
          />
        </div>
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
          <select
            value={filterMDR}
            onChange={(e) => setFilterMDR(e.target.value)}
            className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm"
          >
            <option value="all">All MDR status</option>
            <option value="true">Resistant (MDR+)</option>
            <option value="false">Susceptible (MDR-)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
          <select
            value={filterAnomaly}
            onChange={(e) => setFilterAnomaly(e.target.value)}
            className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm"
          >
            <option value="all">All anomalies</option>
            <option value="true">Anomaly detected</option>
            <option value="false">No anomaly</option>
          </select>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-primary-50 text-primary-600 rounded-full text-sm font-medium hover:bg-primary-100 transition disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
}