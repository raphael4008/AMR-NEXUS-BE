import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bug, AlertTriangle, Pill, MapPin } from 'lucide-react';
import { KPICard } from '../components/ui/KPICard';
import { DataCard } from '../components/ui/DataCard';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import CountyTrendChart from '../components/trends/CountyTrendChart';
import { fetchAlerts } from '../api/endpoints';

export default function CountyOverview({ role }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const { data: alerts } = useQuery({ queryKey: ['alerts', role], queryFn: fetchAlerts });

  return (
    <div className="space-y-5">
      <DataCard>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-600 flex items-center justify-center"><MapPin className="w-5 h-5 text-white" /></div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Kiambu County</h1>
              <p className="text-sm text-[var(--text-secondary)]">County Veterinarian View · Poultry & Livestock AMR Surveillance</p>
            </div>
          </div>
          <div className="flex gap-2">
            <span className="pill pill-cyan">Poultry Focus</span>
            <span className="pill pill-slate">Synthetic Data</span>
          </div>
        </div>
        <div className="flex gap-4 mt-5 flex-wrap">
          {[{ name: 'Ruiru', isolates: 48, resistance: '34%' }, { name: 'Thika', isolates: 22, resistance: '18%' }, { name: 'Gatundu', isolates: 14, resistance: '12%' }].map(sub => (
            <div key={sub.name} className="card p-4 text-center min-w-[110px]">
              <p className="text-[10px] font-semibold uppercase text-[var(--text-muted)]">{sub.name}</p>
              <p className="text-lg font-bold text-[var(--text-primary)] mt-1">{sub.isolates} <span className="text-xs font-normal text-[var(--text-muted)]">isolates</span></p>
              <p className="text-xs font-semibold text-[var(--accent-cyan)]">{sub.resistance} resistance</p>
            </div>
          ))}
        </div>
      </DataCard>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPICard label="Poultry Isolates" value={84} icon={Bug} change={15} />
        <KPICard label="Active Alerts" value={2} icon={AlertTriangle} change={100} changeType="up" />
        <KPICard label="FQ Resistance Rate" value={34} icon={Pill} change={89} changeType="up" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2"><CountyTrendChart /></div>
        <div>
          <DataCard title={`Local Alerts (${alerts?.length || 0})`}>
            {alerts?.map(alert => (
              <button
                key={alert.id}
                onClick={() => { setSelectedAlert(alert.id); setModalOpen(true); }}
                className="w-full text-left p-3 rounded-lg mb-2 border-l-4 border-l-[var(--accent-red)] bg-red-500/5 hover:bg-red-500/10 transition-colors"
              >
                <p className="text-sm font-semibold text-[var(--text-primary)]">{alert.pathogen}</p>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">{alert.summary}</p>
                <p className="text-[10px] text-[var(--text-muted)] mt-1">{alert.subCounty} · Risk: {alert.riskScore}</p>
              </button>
            ))}
          </DataCard>
        </div>
      </div>

      <AlertDetailModal alertId={selectedAlert} role={role} open={modalOpen} onClose={() => { setModalOpen(false); setSelectedAlert(null); }} />
    </div>
  );
}