
import { useEffect, useState } from 'react';
import { AlertTriangle, X, Bell, MessageSquare, ArrowRight } from 'lucide-react';
import { getRiskLabel } from '../../lib/utils';

export default function AlertToast({ alerts = [], onAlertClick, onDismiss }) {
  const [visibleAlerts, setVisibleAlerts] = useState([]);

  useEffect(() => {
    if (alerts.length > 0) {
      const critical = alerts.filter(a => a.riskScore >= 90);
      const high = alerts.filter(a => a.riskScore >= 75 && a.riskScore < 90);
      const toShow = critical.length > 0 ? critical[0] : high.length > 0 ? high[0] : alerts[0];
      
      if (!visibleAlerts.find(v => v.id === toShow.id)) {
        setVisibleAlerts(prev => [...prev, { ...toShow, timestamp: Date.now() }]);
        
        setTimeout(() => {
          setVisibleAlerts(prev => prev.filter(v => v.id !== toShow.id));
        }, 8000);
      }
    }
  }, [alerts]);

  if (visibleAlerts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[200] space-y-3 max-w-sm">
      {visibleAlerts.map(alert => {
        const severity = getRiskLabel(alert.riskScore);
        const isCritical = severity === 'Critical';
        const isHigh = severity === 'High';

        // Theme-aware colors using CSS variables
        const bgColor = isCritical
          ? 'bg-red-500/10 backdrop-blur-xl border border-red-500/20'
          : isHigh
          ? 'bg-orange-500/10 backdrop-blur-xl border border-orange-500/20'
          : 'bg-[var(--accent)]/10 backdrop-blur-xl border border-[var(--accent)]/20';

        const iconColor = isCritical
          ? 'text-red-500'
          : isHigh
          ? 'text-orange-500'
          : 'text-[var(--accent)]';

        const iconBg = isCritical
          ? 'bg-red-500/20'
          : isHigh
          ? 'bg-orange-500/20'
          : 'bg-[var(--accent)]/20';

        const pillClass = isCritical
          ? 'bg-red-500/20 text-red-500 border border-red-500/30'
          : isHigh
          ? 'bg-orange-500/20 text-orange-500 border border-orange-500/30'
          : 'bg-[var(--accent)]/20 text-[var(--accent)] border border-[var(--accent)]/30';

        return (
          <div
            key={alert.timestamp}
            className={`${bgColor} rounded-xl p-4 shadow-xl animate-in slide-in-from-right-full duration-300 bg-[var(--bg-card)]/90`}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className={`w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                <AlertTriangle className={`w-4 h-4 ${iconColor}`} strokeWidth={1.5} />
              </div>

              <div className="flex-1 min-w-0">
                {/* Header */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${pillClass}`}>
                        {severity}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">
                        Score: {alert.riskScore}
                      </span>
                    </div>
                    <p className="text-[12px] font-semibold text-[var(--text-primary)] mt-1.5">
                      {alert.pathogen}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-0.5 line-clamp-2 leading-relaxed">
                      {alert.summary}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setVisibleAlerts(prev => prev.filter(v => v.timestamp !== alert.timestamp));
                      onDismiss?.(alert);
                    }}
                    className="p-1 rounded-lg hover:bg-[var(--bg-primary)]/50 transition-colors flex-shrink-0"
                  >
                    <X className="w-3.5 h-3.5 text-[var(--text-muted)]" strokeWidth={1.5} />
                  </button>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 mt-3">
                  <button
                    onClick={() => {
                      onAlertClick?.(alert);
                      setVisibleAlerts(prev => prev.filter(v => v.timestamp !== alert.timestamp));
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--accent)] text-white text-[11px] font-semibold hover:opacity-90 transition-opacity"
                  >
                    <Bell className="w-3 h-3" strokeWidth={1.5} />
                    Investigate
                    <ArrowRight className="w-3 h-3" strokeWidth={1.5} />
                  </button>
                  <button
                    onClick={() => {
                      const event = new CustomEvent('sms-notification', { detail: alert });
                      window.dispatchEvent(event);
                      setVisibleAlerts(prev => prev.filter(v => v.timestamp !== alert.timestamp));
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border)] text-[11px] font-medium text-[var(--text-muted)] hover:bg-[var(--bg-primary)]/30 transition-colors"
                  >
                    <MessageSquare className="w-3 h-3" strokeWidth={1.5} />
                    Send SMS
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
