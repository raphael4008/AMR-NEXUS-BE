import { AlertTriangle, MapPin, Clock, ChevronRight } from 'lucide-react';
import { formatTimeAgo } from '../../lib/utils';

export default function AlertFeedPanel({ alerts = [], onAlertClick }) {
  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-[var(--border-primary)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-red-500/10 flex items-center justify-center">
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--accent-red)]" />
          </div>
          <span className="section-label">Alert Intelligence</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="live-pulse" />
          <span className="pill pill-red text-[10px]">{alerts.length} active</span>
        </div>
      </div>

      <div className="divide-y divide-[var(--border-primary)] max-h-[500px] overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="p-6 text-center">
            <div className="w-10 h-10 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center mx-auto mb-2">
              <AlertTriangle className="w-5 h-5 text-[var(--text-muted)]" />
            </div>
            <p className="text-sm text-[var(--text-muted)]">No active alerts</p>
          </div>
        ) : (
          alerts.map(alert => {
            const isCritical = alert.riskScore >= 90;
            const isHigh = alert.riskScore >= 75 && alert.riskScore < 90;
            return (
              <button
                key={alert.id}
                onClick={() => onAlertClick(alert)}
                className="w-full text-left p-4 hover:bg-[var(--bg-tertiary)] transition-colors group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-cyan)] transition-colors">
                    {alert.pathogen}
                  </span>
                  <span className={`pill text-[10px] ${isCritical ? 'pill-red' : isHigh ? 'pill-red' : 'pill-cyan'}`}>
                    {alert.riskScore}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mb-2 line-clamp-2 leading-relaxed">
                  {alert.summary}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{alert.subCounty}</span>
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTimeAgo(alert.triggeredAt)}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--accent-cyan)] transition-colors" />
                </div>
                {/* Risk bar */}
                <div className="mt-2 h-1 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isCritical ? 'bg-[var(--accent-red)]' : isHigh ? 'bg-orange-500' : 'bg-[var(--accent-cyan)]'
                    }`}
                    style={{ width: `${alert.riskScore}%` }}
                  />
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}