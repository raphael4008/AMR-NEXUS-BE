import { MagnifyingGlassIcon, ArrowPathIcon, FunnelIcon } from '@heroicons/react/24/outline';

export default function AnalyticsFilters({
  startDate,
  endDate,
  setStartDate,
  setEndDate,
  selectedCounty,
  setSelectedCounty,
  selectedPathogen,
  setSelectedPathogen,
  autoRefresh,
  setAutoRefresh,
  onRefresh,
  loading,
  countiesList,
  pathogensList,
}) {
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Start Date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full rounded-full border px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">End Date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full rounded-full border px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">County</label>
          <select value={selectedCounty} onChange={(e) => setSelectedCounty(e.target.value)} className="w-full rounded-full border px-3 py-1.5 text-sm">
            <option value="">All counties</option>
            {countiesList.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Pathogen</label>
          <select value={selectedPathogen} onChange={(e) => setSelectedPathogen(e.target.value)} className="w-full rounded-full border px-3 py-1.5 text-sm">
            <option value="">All pathogens</option>
            {pathogensList.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} className="rounded" />
            <span className="text-sm text-gray-600">Auto-refresh (30s)</span>
          </label>
        </div>
        <div className="flex items-end">
          <button onClick={onRefresh} disabled={loading} className="flex items-center justify-center gap-2 w-full px-4 py-1.5 bg-primary-600 text-white rounded-full text-sm">
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
    </div>
  );
}