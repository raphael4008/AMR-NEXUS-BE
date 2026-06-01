import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, AlertTriangle, Building2, Bug } from 'lucide-react';
import { KPICard } from '../components/ui/KPICard';
import { DataCard } from '../components/ui/DataCard';
import CountyChoroplethMap from '../components/map/CountyChoroplethMap';
import MapTimeSlider from '../components/map/MapTimeSlider';
import AlertFeedPanel from '../components/alerts/AlertFeedPanel';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import AlertToast from '../components/alerts/AlertToast';
import SMSNotificationModal from '../components/alerts/SMSNotificationModal';
import AnomalySummary from '../components/trends/AnomalySummary';
import { fetchSummary, fetchAlerts } from '../api/endpoints';

export default function NationalOverview({ role, darkMode }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const { data: summary } = useQuery({ queryKey: ['summary', role], queryFn: fetchSummary });
  const { data: alerts } = useQuery({ queryKey: ['alerts', role], queryFn: fetchAlerts });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">National AMR Surveillance</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-0.5">AI-Powered Early Warning Platform · Synthetic Data Demonstration</p>
        </div>
        <span className="pill pill-slate">Updated just now</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Isolates" value={summary?.totalIsolates || 527} icon={FlaskConical} change={12} sparkline={[45,52,49,58,62,55,68,72]} />
        <KPICard label="Active Anomalies" value={summary?.activeAnomalies || 7} icon={AlertTriangle} change={28} changeType="up" sparkline={[2,3,2,4,5,3,6,7]} />
        <KPICard label="Counties Reporting" value={summary?.countiesReporting || 12} icon={Building2} change={8} sparkline={[8,9,9,10,10,11,11,12]} />
        <KPICard label="One Health Signals" value={summary?.oneHealthSignals || 3} icon={Bug} change={50} sparkline={[0,1,1,1,2,1,2,3]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        <div className="lg:col-span-3 space-y-4">
          <DataCard title="Surveillance Heatmap" className="p-0 overflow-hidden">
            {/* Fixed height for the dashboard map */}
            <div style={{ height: '450px' }}>
              <CountyChoroplethMap
                darkMode={darkMode}
                onCountyClick={(props) => {
                  const alert = alerts?.find(a => a.county === props.county);
                  if (alert) { setSelectedAlert(alert.id); setModalOpen(true); }
                }}
              />
            </div>
          </DataCard>
          <MapTimeSlider />
        </div>
        <div className="space-y-4">
          <AlertFeedPanel alerts={alerts} onAlertClick={(alert) => { setSelectedAlert(alert.id); setModalOpen(true); }} />
          <AnomalySummary anomalies={alerts} onAnomalyClick={(a) => { setSelectedAlert(a.id); setModalOpen(true); }} />
        </div>
      </div>

      <AlertDetailModal alertId={selectedAlert} role={role} open={modalOpen} onClose={() => { setModalOpen(false); setSelectedAlert(null); }} />
      <AlertToast alerts={alerts} onAlertClick={(alert) => { setSelectedAlert(alert.id); setModalOpen(true); }} />
      <SMSNotificationModal />
    </div>
  );
}