import { useState } from 'react';
import { DataCard } from '../components/ui/DataCard';
import TrendChart from '../components/trends/TrendChart';
import TrendFilters from '../components/trends/TrendFilters';

export default function NationalTrends() {
  const [filters, setFilters] = useState({ pathogen: 'Klebsiella pneumoniae', drug: 'Carbapenem', region: 'Nairobi', months: 12 });
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)] tracking-tight">Trend Analysis</h1>
        <p className="text-[12px] text-[var(--text-tertiary)] mt-0.5">AI-powered resistance trajectory analysis with anomaly detection</p>
      </div>
      <TrendFilters filters={filters} onChange={setFilters} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <TrendChart pathogen={filters.pathogen} drug={filters.drug} region={filters.region} months={filters.months} />
        <DataCard title="Anomaly Summary"><p className="text-[13px] text-[var(--text-secondary)]">Select pathogen and region to view detected anomalies.</p></DataCard>
      </div>
    </div>
  );
}
