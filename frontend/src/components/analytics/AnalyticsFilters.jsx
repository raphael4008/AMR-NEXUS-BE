import { MagnifyingGlassIcon, ArrowPathIcon, FunnelIcon } from '@heroicons/react/24/outline';
import Select from 'react-select';

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
  // Convert lists to react-select options
  const countyOptions = countiesList.map(c => ({ value: c, label: c }));
  const pathogenOptions = pathogensList.map(p => ({ value: p, label: p }));

  // Styles for react-select – floating menus with high z-index
  const selectStyles = {
    control: (base) => ({
      ...base,
      borderRadius: '9999px',
      borderColor: '#d1d5db',
      boxShadow: 'none',
      '&:hover': { borderColor: '#9ca3af' },
      minHeight: '36px',
      height: '36px',
    }),
    menu: (base) => ({
      ...base,
      borderRadius: '12px',
      marginTop: '4px',
      zIndex: 9999,
    }),
    menuPortal: (base) => ({ ...base, zIndex: 9999 }),
    dropdownIndicator: (base) => ({ ...base, padding: '4px' }),
    clearIndicator: (base) => ({ ...base, padding: '4px' }),
    valueContainer: (base) => ({ ...base, padding: '0 8px' }),
    input: (base) => ({ ...base, margin: 0, padding: 0 }),
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
        {/* Start Date */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full rounded-full border px-3 py-1.5 text-sm"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full rounded-full border px-3 py-1.5 text-sm"
          />
        </div>

        {/* County – searchable dropdown */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">County</label>
          <Select
            options={countyOptions}
            value={countyOptions.find(o => o.value === selectedCounty) || null}
            onChange={(option) => setSelectedCounty(option?.value || '')}
            placeholder="Search county..."
            isClearable
            styles={selectStyles}
            menuPortalTarget={document.body}
          />
        </div>

        {/* Pathogen – searchable dropdown */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Pathogen</label>
          <Select
            options={pathogenOptions}
            value={pathogenOptions.find(o => o.value === selectedPathogen) || null}
            onChange={(option) => setSelectedPathogen(option?.value || '')}
            placeholder="Search pathogen..."
            isClearable
            styles={selectStyles}
            menuPortalTarget={document.body}
          />
        </div>

        {/* Auto-refresh toggle */}
        <div className="flex items-end">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-600">Auto-refresh (30s)</span>
          </label>
        </div>

        {/* Refresh button */}
        <div className="flex items-end">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center justify-center gap-2 w-full px-4 py-1.5 bg-primary-600 text-white rounded-full text-sm hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
    </div>
  );
}