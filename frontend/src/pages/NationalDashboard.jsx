import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, AlertTriangle, Building2, Bug, MapPin } from 'lucide-react';
import { KPICard } from '../components/ui/KPICard';
import { DataCard } from '../components/ui/DataCard';
import CountyChoroplethMap from '../components/map/CountyChoroplethMap';
import AlertFeedPanel from '../components/alerts/AlertFeedPanel';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { fetchSummary, fetchAlerts } from '../api/endpoints';

export default function NationalDashboard({ role }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: summary } = useQuery({
    queryKey: ['summary', role],
    queryFn: fetchSummary,
  });

  const { data: alerts } = useQuery({
    queryKey: ['alerts', role],
    queryFn: fetchAlerts,
  });

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          National AMR Surveillance Overview
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          AI-Powered Early Warning & Decision-Support Platform
          <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            Synthetic Data Demo
          </span>
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Isolates"
          value={summary?.totalIsolates || 527}
          icon={FlaskConical}
          trend="up"
          trendValue={12}
          colorClass="medical"
          sparkline={[45, 52, 49, 58, 62, 55, 68, 72]}
          subtitle="Human + Poultry sectors"
        />
        <KPICard
          title="Active Anomalies"
          value={summary?.activeAnomalies || 7}
          icon={AlertTriangle}
          trend="up"
          trendValue={28}
          colorClass="alert"
          sparkline={[2, 3, 2, 4, 5, 3, 6, 7]}
          subtitle="Requiring attention"
        />
        <KPICard
          title="Counties Reporting"
          value={summary?.countiesReporting || 12}
          icon={Building2}
          trend="up"
          trendValue={8}
          colorClass="info"
          sparkline={[8, 9, 9, 10, 10, 11, 11, 12]}
          subtitle="Out of 47 counties"
        />
        <KPICard
          title="One Health Signals"
          value={summary?.oneHealthSignals || 3}
          icon={Bug}
          trend="up"
          trendValue={50}
          colorClass="agriculture"
          sparkline={[0, 1, 1, 1, 2, 1, 2, 3]}
          subtitle="Human-Animal overlap"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DataCard className="p-0 overflow-hidden" hover={false}>
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-500" />
                <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">
                  Surveillance Heatmap
                </h3>
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                INTERACTIVE
              </span>
            </div>
            <div className="h-[500px]">
              <CountyChoroplethMap
                onCountyClick={(props) => {
                  const alert = alerts?.find(a => a.county === props.county);
                  if (alert) {
                    setSelectedAlert(alert.id);
                    setModalOpen(true);
                  }
                }}
              />
            </div>
          </DataCard>
        </div>

        <div>
          <AlertFeedPanel
            alerts={alerts}
            onAlertClick={(alert) => {
              setSelectedAlert(alert.id);
              setModalOpen(true);
            }}
          />
        </div>
      </div>

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
