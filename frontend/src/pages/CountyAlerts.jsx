
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AlertFeedPanel from '../components/alerts/AlertFeedPanel';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { fetchAlerts } from '../api/endpoints';

export default function CountyAlerts({ role }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const { data: alerts } = useQuery({ queryKey: ['alerts', role], queryFn: fetchAlerts });

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)] tracking-tight">
          Local Alerts
        </h1>
        <p className="text-[12px] text-[var(--text-muted)] mt-1">
          Kiambu County · Poultry AMR Alerts
        </p>
      </div>

      {/* Alert Feed Panel */}
      <div className="max-w-2xl">
        <AlertFeedPanel 
          alerts={alerts} 
          onAlertClick={(alert) => { 
            setSelectedAlert(alert.id); 
            setModalOpen(true); 
          }} 
        />
      </div>

      {/* Alert Detail Modal */}
      <AlertDetailModal 
        alertId={selectedAlert} 
        role={role} 
        open={modalOpen} 
        onClose={() => { 
          setModalOpen(false); 
          setSelectedAlert(null); 
        }} 
      />
    </div>
  );
}
