import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AlertFeedPanel from '../components/alerts/AlertFeedPanel';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { fetchAlerts } from '../api/endpoints';

export default function NationalAlerts({ role }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const { data: alerts } = useQuery({ queryKey: ['alerts', role], queryFn: fetchAlerts });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)] tracking-tight">Risk Alerts</h1>
        <p className="text-[12px] text-[var(--text-tertiary)] mt-0.5">AI-detected AMR alerts requiring attention</p>
      </div>
      <div className="max-w-2xl"><AlertFeedPanel alerts={alerts} onAlertClick={(alert) => { setSelectedAlert(alert.id); setModalOpen(true); }} /></div>
      <AlertDetailModal alertId={selectedAlert} role={role} open={modalOpen} onClose={() => { setModalOpen(false); setSelectedAlert(null); }} />
    </div>
  );
}
