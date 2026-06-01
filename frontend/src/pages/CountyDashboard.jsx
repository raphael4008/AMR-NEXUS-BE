import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Bug, 
  AlertTriangle, 
  Pill,
  MapPin,
  TrendingUp,
} from 'lucide-react';
import { KPICard } from '../components/ui/KPICard';
import { DataCard } from '../components/ui/DataCard';
import AlertDetailModal from '../components/alerts/AlertDetailModal';
import { fetchSummary, fetchAlerts } from '../api/endpoints';

export default function CountyDashboard({ role }) {
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

  const trendData = [18, 19, 20, 22, 23, 28, 32, 34];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];

  return (
    <div className="space-y-6">
      {/* County Header - Updated to use theme variables */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-glass)] rounded-[24px] p-5 shadow-lg transition-all">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <MapPin className="w-6 h-6 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                Kiambu County
              </h1>
              <p className="text-sm text-[var(--text-muted)]">
                County Veterinarian View · Poultry & Livestock AMR Surveillance
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              Poultry Focus
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[var(--bg-primary)]/50 text-[var(--text-muted)] border border-[var(--border)]">
              Synthetic Data
            </span>
          </div>
        </div>

        <div className="flex gap-4 mt-6 flex-wrap">
          {[
            { name: 'Ruiru', isolates: 48, resistance: '34%' },
            { name: 'Thika', isolates: 22, resistance: '18%' },
            { name: 'Gatundu', isolates: 14, resistance: '12%' },
          ].map((sub) => (
            <div key={sub.name} className="bg-[var(--bg-primary)]/30 rounded-xl px-4 py-3 border border-[var(--border-glass)]">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">{sub.name}</p>
              <div className="flex gap-3 mt-1">
                <span className="text-sm text-[var(--text-primary)]">
                  <strong>{sub.isolates}</strong> isolates
                </span>
                <span className="text-sm font-semibold text-amber-500">{sub.resistance}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPICard
          title="Poultry Isolates"
          value={84}
          icon={Bug}
          trend="up"
          trendValue={15}
          colorClass="agriculture"
          subtitle="Across 3 monitored farms"
        />
        <KPICard
          title="Active Alerts"
          value={2}
          icon={AlertTriangle}
          trend="up"
          trendValue={100}
          colorClass="alert"
          subtitle="Requiring immediate action"
        />
        <KPICard
          title="FQ Resistance Rate"
          value={34}
          icon={Pill}
          trend="up"
          trendValue={89}
          colorClass="agriculture"
          subtitle="Fluoroquinolone in poultry"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-[var(--bg-card)] border border-[var(--border-glass)] rounded-[24px] p-5 shadow-lg transition-all">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-amber-500" strokeWidth={1.5} />
              <h3 className="font-semibold text-sm text-[var(--text-primary)]">
                Resistance Trend — Fluoroquinolone · E. coli
              </h3>
            </div>
            
            <svg width="100%" height="200" className="mb-2">
              <defs>
                <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.02" />
                </linearGradient>
              </defs>
              {(() => {
                const max = Math.max(...trendData);
                const min = Math.min(...trendData);
                const range = max - min || 1;
                const padding = 20;
                const w = 100 / (trendData.length - 1);
                
                const points = trendData.map((v, i) => 
                  `${i * w}%,${padding + (1 - (v - min) / range) * (180 - padding * 2)}`
                ).join(' ');
                
                return (
                  <>
                    <polygon points={`0,200 ${points} 100,200`} fill="url(#trendGrad)" />
                    <polyline points={points} fill="none" stroke="#F59E0B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    <circle 
                      cx={`${(trendData.length - 1) * w}%`} 
                      cy={padding + (1 - (trendData[trendData.length - 1] - min) / range) * (180 - padding * 2)} 
                      r="4" fill="var(--bg-card)" stroke="#F59E0B" strokeWidth="2.5" 
                    />
                  </>
                );
              })()}
            </svg>
            
            <div className="flex justify-between px-1">
              {months.map((m, i) => (
                <span key={i} className={`text-[10px] ${i >= 5 ? 'text-red-500 font-semibold' : 'text-[var(--text-muted)]'}`}>
                  {m}
                </span>
              ))}
            </div>

            <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" strokeWidth={1.5} />
              <div>
                <p className="text-sm font-semibold text-red-600 dark:text-red-400">
                  Anomaly Detected — Sharp Resistance Increase
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Fluoroquinolone resistance in poultry E. coli rose from 22% to 34% in the last 3 months.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="bg-[var(--bg-card)] border border-[var(--border-glass)] rounded-[24px] p-5 shadow-lg transition-all">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-500" strokeWidth={1.5} />
              <h3 className="font-semibold text-sm text-[var(--text-primary)]">
                Local Alerts
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-500 border border-red-500/20">
                {alerts?.length || 0}
              </span>
            </div>
            
            {alerts?.map(alert => (
              <button
                key={alert.id}
                onClick={() => {
                  setSelectedAlert(alert.id);
                  setModalOpen(true);
                }}
                className="w-full text-left p-3 rounded-xl mb-2 transition-all hover:translate-x-1 bg-red-500/5 border-l-4 border-red-500"
              >
                <p className="text-sm font-semibold text-[var(--text-primary)]">
                  {alert.pathogen}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  {alert.summary}
                </p>
                <p className="text-[10px] text-[var(--text-muted)] mt-1">
                  {alert.subCounty} · Risk: {alert.riskScore}
                </p>
              </button>
            ))}
          </div>
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
