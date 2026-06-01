import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataCard } from '../components/ui/DataCard';
import CountyChoroplethMap from '../components/map/CountyChoroplethMap';
import MapFilters from '../components/map/MapFilters';
import MapTimeSlider from '../components/map/MapTimeSlider';
import CountyDetailPanel from '../components/map/CountyDetailPanel';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { fetchAlerts } from '../api/endpoints';

export default function NationalMap({ role, darkMode }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [filters, setFilters] = useState({ metric: 'carbapenem', sector: 'all' });
  const [timeMonth, setTimeMonth] = useState(23);
  const [selectedCounty, setSelectedCounty] = useState(null);

  const { data: alerts } = useQuery({ queryKey: ['alerts', role], queryFn: fetchAlerts });

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Surveillance Map</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-0.5">
            Interactive county-level resistance heatmap
          </p>
        </div>
        <MapFilters filters={filters} onChange={setFilters} />
      </div>

      {/* Map takes remaining space exactly */}
      <div className="flex-1 relative" style={{ minHeight: 0 }}>
        <DataCard className="absolute inset-0 p-0 overflow-hidden">
          <CountyChoroplethMap
            darkMode={darkMode}
            timeMonth={timeMonth}
            onCountyClick={(props) => setSelectedCounty(props)}
          />
        </DataCard>

        <CountyDetailPanel
          county={selectedCounty}
          alerts={alerts || []}
          onClose={() => setSelectedCounty(null)}
        />
      </div>

      <MapTimeSlider onTimeChange={(month) => setTimeMonth(month)} />

      <AlertDetailModal
        alertId={selectedAlert}
        role={role}
        open={modalOpen}
        onClose={() => { setModalOpen(false); setSelectedAlert(null); }}
      />
    </div>
  );
}