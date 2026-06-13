import { useState, useEffect } from 'react';
import { FunnelIcon, XMarkIcon, BookmarkIcon } from '@heroicons/react/24/outline';

const SAVED_VIEWS_KEY = 'history_saved_views';

export default function HistoryAdvancedFilters({
  filters,
  setFilters,
  onRefresh,
  loading,
}) {
  const [savedViews, setSavedViews] = useState([]);
  const [viewName, setViewName] = useState('');

  useEffect(() => {
    const stored = localStorage.getItem(SAVED_VIEWS_KEY);
    if (stored) setSavedViews(JSON.parse(stored));
  }, []);

  const saveCurrentView = () => {
    if (!viewName) return;
    const newView = { name: viewName, filters: { ...filters } };
    const updated = [...savedViews, newView];
    setSavedViews(updated);
    localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(updated));
    setViewName('');
  };

  const loadView = (view) => {
    setFilters(view.filters);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      mdr: 'all',
      anomaly: 'all',
      pathogen: '',
      county: '',
      antibioticClass: '',
      startDate: '',
      endDate: '',
    });
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-4">
      <div className="flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs text-gray-500 mb-1">Pathogen</label>
          <input
            value={filters.pathogen}
            onChange={(e) => setFilters({...filters, pathogen: e.target.value})}
            placeholder="e.g., ECO"
            className="w-full rounded-full border px-3 py-1.5 text-sm"
          />
        </div>
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs text-gray-500 mb-1">County</label>
          <input
            value={filters.county}
            onChange={(e) => setFilters({...filters, county: e.target.value})}
            placeholder="e.g., Nairobi"
            className="w-full rounded-full border px-3 py-1.5 text-sm"
          />
        </div>
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs text-gray-500 mb-1">Antibiotic Class</label>
          <select
            value={filters.antibioticClass}
            onChange={(e) => setFilters({...filters, antibioticClass: e.target.value})}
            className="w-full rounded-full border px-3 py-1.5 text-sm"
          >
            <option value="">All</option>
            <option>Fluoroquinolone</option>
            <option>Penicillin</option>
            <option>Carbapenem</option>
            <option>Tetracycline</option>
          </select>
        </div>
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs text-gray-500 mb-1">Start Date</label>
          <input type="date" value={filters.startDate} onChange={(e) => setFilters({...filters, startDate: e.target.value})} className="w-full rounded-full border px-3 py-1.5 text-sm" />
        </div>
        <div className="flex-1 min-w-[150px]">
          <label className="block text-xs text-gray-500 mb-1">End Date</label>
          <input type="date" value={filters.endDate} onChange={(e) => setFilters({...filters, endDate: e.target.value})} className="w-full rounded-full border px-3 py-1.5 text-sm" />
        </div>
        <button onClick={onRefresh} disabled={loading} className="px-4 py-1.5 bg-primary-600 text-white rounded-full text-sm">Apply</button>
        <button onClick={clearFilters} className="px-4 py-1.5 border rounded-full text-sm">Clear</button>
      </div>

      {/* Saved views */}
      <div className="border-t pt-3 flex flex-wrap items-center gap-2">
        <BookmarkIcon className="h-4 w-4 text-gray-400" />
        <span className="text-xs text-gray-500">Saved views:</span>
        {savedViews.map(v => (
          <button key={v.name} onClick={() => loadView(v)} className="text-xs bg-gray-100 px-2 py-1 rounded-full hover:bg-gray-200">{v.name}</button>
        ))}
        <input value={viewName} onChange={e => setViewName(e.target.value)} placeholder="New view name" className="text-xs border rounded-full px-2 py-1 w-28" />
        <button onClick={saveCurrentView} disabled={!viewName} className="text-xs text-primary-600">Save</button>
      </div>
    </div>
  );
}