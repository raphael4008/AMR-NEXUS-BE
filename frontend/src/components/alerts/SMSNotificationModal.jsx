import { useState, useEffect } from 'react';
import { X, MessageSquare, CheckCircle2, Phone, Clock, MapPin, Send } from 'lucide-react';

export default function SMSNotificationModal() {
  const [open, setOpen] = useState(false);
  const [alert, setAlert] = useState(null);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    const handler = (event) => {
      setAlert(event.detail);
      setOpen(true);
      setSent(false);
      
      setTimeout(() => {
        setSent(true);
      }, 2000);
    };

    window.addEventListener('sms-notification', handler);
    return () => window.removeEventListener('sms-notification', handler);
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setOpen(false)} />
      
      {/* Modal - using theme variables */}
      <div className="relative bg-[var(--bg-card)] border border-[var(--border-glass)] rounded-[24px] max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200 overflow-hidden">
        {/* Close button */}
        <button
          onClick={() => setOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-[var(--bg-primary)]/50 transition-colors text-[var(--text-muted)] z-10"
        >
          <X className="w-4 h-4" strokeWidth={1.5} />
        </button>

        <div className="p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-lg shadow-cyan-500/40">
              <MessageSquare className="w-5 h-5 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="font-semibold text-[15px] text-[var(--text-primary)]">SMS Notification</h3>
              <p className="text-[11px] text-[var(--text-muted)]">Africa's Talking Simulator</p>
            </div>
          </div>

          {/* Phone Preview - Dark preview card for both themes */}
          <div className="bg-[#0A0E17] rounded-2xl p-4 mb-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider">SMS Preview</span>
              <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
                <Clock className="w-2.5 h-2.5" strokeWidth={1.5} />
                Now
              </span>
            </div>
            
            <div className="bg-cyan-500/10 rounded-xl p-3.5 border border-cyan-500/20">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-5 h-5 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Send className="w-2.5 h-2.5 text-cyan-400" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">AMR-Nexus Alert</p>
                  {alert && (
                    <p className="text-[13px] text-white mt-1 leading-relaxed">
                      <span className={`font-bold ${alert.riskScore >= 90 ? 'text-red-400' : 'text-amber-400'}`}>
                        {alert.riskScore >= 90 ? 'CRITICAL' : 'HIGH'}
                      </span>
                      {' '}AMR Alert: {alert.pathogen} — {alert.drugClass} resistance detected in {alert.subCounty}. Risk Score: {alert.riskScore}/100. {alert.summary} Please check dashboard for guidance.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Recipients */}
          {alert && (
            <div className="space-y-2 mb-5">
              <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
                <MapPin className="w-3.5 h-3.5" strokeWidth={1.5} />
                <span>Sending to <span className="font-medium text-[var(--text-primary)]">{alert.county} County AMR Focal Person</span></span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
                <Phone className="w-3.5 h-3.5" strokeWidth={1.5} />
                <span className="font-mono">+254 7XX XXX XXX</span>
                <span className="px-2 py-0.5 rounded-full bg-[var(--bg-primary)]/50 text-[9px] text-[var(--text-muted)] uppercase tracking-wider">simulated</span>
              </div>
            </div>
          )}

          {/* Status */}
          <div
            className={`p-4 rounded-xl flex items-center gap-3 transition-all duration-500 ${
              sent
                ? 'bg-green-500/10 border border-green-500/20'
                : 'bg-amber-500/10 border border-amber-500/20'
            }`}
          >
            {sent ? (
              <>
                <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-4 h-4 text-green-500" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-green-500">SMS Sent Successfully</p>
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5">Notification delivered to county focal person</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <div className="w-4 h-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-amber-500">Sending SMS...</p>
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5">Connecting to Africa's Talking sandbox</p>
                </div>
              </>
            )}
          </div>

          {/* Close button */}
          <button
            onClick={() => setOpen(false)}
            className="w-full mt-4 py-2.5 rounded-xl bg-[var(--accent)] text-white text-[13px] font-semibold hover:opacity-90 transition-opacity"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
