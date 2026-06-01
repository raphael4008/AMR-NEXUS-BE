export default function TrendFilters({ filters, onChange }) {
  const selectClasses = "bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] cursor-pointer hover:border-[var(--accent-cyan)]/50 focus:outline-none focus:border-[var(--accent-cyan)] transition-colors appearance-none";

  return (
    <div className="flex flex-wrap gap-3">
      <select value={filters.pathogen} onChange={(e) => onChange({ ...filters, pathogen: e.target.value })} className={selectClasses}>
        <option>Klebsiella pneumoniae</option>
        <option>Escherichia coli</option>
        <option>Acinetobacter baumannii</option>
      </select>
      <select value={filters.drug} onChange={(e) => onChange({ ...filters, drug: e.target.value })} className={selectClasses}>
        <option>Carbapenem</option>
        <option>ESBL</option>
        <option>Fluoroquinolone</option>
      </select>
      <select value={filters.region} onChange={(e) => onChange({ ...filters, region: e.target.value })} className={selectClasses}>
        <option>Nairobi</option>
        <option>Mombasa</option>
        <option>Kiambu</option>
      </select>
    </div>
  );
}