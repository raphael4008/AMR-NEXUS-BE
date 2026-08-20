import { MagnifyingGlassIcon, ArrowPathIcon, FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import Select from 'react-select';
import { useState, useEffect } from 'react';

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
  countiesList = [],
  pathogensList = [],
}) {
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  useEffect(() => {
    let count = 0;
    if (startDate) count++;
    if (endDate) count++;
    if (selectedCounty) count++;
    if (selectedPathogen) count++;
    setActiveFilterCount(count);
  }, [startDate, endDate, selectedCounty, selectedPathogen]);

  const handleReset = () => {
    setStartDate('');
    setEndDate('');
    setSelectedCounty('');
    setSelectedPathogen('');
  };

  const countyOptions = countiesList.map(c => ({ value: c, label: c }));
  const pathogenOptions = pathogensList.map(p => ({ value: p, label: p }));

  const selectStyles = {
    control: (base) => ({
      ...base,
      borderRadius: '9999px',
      borderColor: '#d1d5db',
      boxShadow: 'none',
      '&:hover': { borderColor: '#9ca3af' },
      minHeight: '36px',
      height: '36px',
      backgroundColor: '#ffffff',
    }),
    menu: (base) => ({
      ...base,
      borderRadius: '12px',
      marginTop: '4px',
      zIndex: 9999,
      boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
    }),
    menuPortal: (base) => ({ ...base, zIndex: 9999 }),
    dropdownIndicator: (base) => ({ ...base, padding: '4px' }),
    clearIndicator: (base) => ({ ...base, padding: '4px' }),
    valueContainer: (base) => ({ ...base, padding: '0 8px' }),
    input: (base) => ({ ...base, margin: 0, padding: 0 }),
    placeholder: (base) => ({ ...base, color: '#9ca3af', fontSize: '0.875rem' }),
    option: (base, { isFocused, isSelected }) => ({
      ...base,
      backgroundColor: isSelected ? '#2563eb' : isFocused ? '#eff6ff' : '#ffffff',
      color: isSelected ? '#ffffff' : '#1f2937',
      padding: '8px 16px',
      cursor: 'pointer',
    }),
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-5 w-5 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filters</span>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
              {activeFilterCount} active
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={handleReset}
            className="text-xs text-gray-500 hover:text-red-600 transition-colors flex items-center gap-1"
          >
            <XMarkIcon className="h-4 w-4" />
            Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full rounded-full border border-gray-300 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full rounded-full border border-gray-300 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
          />
        </div>

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
            classNamePrefix="react-select"
          />
        </div>

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
            classNamePrefix="react-select"
          />
        </div>

        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            Auto-refresh (30s)
          </label>
        </div>

        <div className="flex items-end gap-2">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-1.5 bg-primary-600 text-white rounded-full text-sm hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
    </div>
  );
}