import { SlidersHorizontal, Layers } from 'lucide-react';

export default function MapFilters({ filters, onChange }) {
  const selectClasses = "bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] cursor-pointer hover:border-[var(--accent-cyan)]/50 focus:outline-none focus:border-[var(--accent-cyan)] transition-colors appearance-none";

  return (
    <div className="flex gap-2">
      <div className="flex items-center gap-1.5">
        <SlidersHorizontal className="w-4 h-4 text-[var(--text-muted)]" />
        <select value={filters.metric} onChange={(e) => onChange({ ...filters, metric: e.target.value })} className={selectClasses}>
          <option value="carbapenem">Carbapenem</option>
          <option value="esbl">ESBL</option>
          <option value="fluoroquinolone">Fluoroquinolone</option>
        </select>
      </div>
      <div className="flex items-center gap-1.5">
        <Layers className="w-4 h-4 text-[var(--text-muted)]" />
        <select value={filters.sector} onChange={(e) => onChange({ ...filters, sector: e.target.value })} className={selectClasses}>
          <option value="all">All Sectors</option>
          <option value="human">Human</option>
          <option value="poultry">Poultry</option>
          <option value="environment">Environment</option>
        </select>
      </div>
    </div>
  );
}