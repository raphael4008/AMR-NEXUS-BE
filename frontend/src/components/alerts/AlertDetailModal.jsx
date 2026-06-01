import { useQuery } from '@tanstack/react-query';
import {
  X, AlertTriangle, Lightbulb, CheckCircle2, FileText,
  Loader2, MapPin, Clock, FlaskConical, ExternalLink,
  TrendingUp, BarChart3, Send
} from 'lucide-react';
import { fetchAlertDetail, fetchAlertExplanation, fetchAlertGuidance } from '../../api/endpoints';
import { getRiskLabel } from '../../lib/utils';
import TrendChart from '../trends/TrendChart';

export default function AlertDetailModal({ alertId, role, open, onClose }) {
  const { data: alert, isLoading: alertLoading } = useQuery({
    queryKey: ['alert', alertId],
    queryFn: () => fetchAlertDetail(alertId),
    enabled: !!alertId && open,
  });
  const { data: explanation, isLoading: explLoading } = useQuery({
    queryKey: ['alert-explanation', alertId],
    queryFn: () => fetchAlertExplanation(alertId),
    enabled: !!alertId && open,
  });
  const { data: guidance, isLoading: guidanceLoading } = useQuery({
    queryKey: ['alert-guidance', alertId, role],
    queryFn: () => fetchAlertGuidance({ alertId, role }),
    enabled: !!alertId && open,
  });

  if (!open) return null;

  const isLoading = alertLoading || explLoading || guidanceLoading;
  const severity = alert ? getRiskLabel(alert.riskScore) : 'Moderate';
  const isCritical = alert?.riskScore >= 90;
  const isHigh = alert?.riskScore >= 75 && alert?.riskScore < 90;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-[var(--accent-cyan)]" />
            <p className="text-sm text-[var(--text-muted)]">Loading alert intelligence...</p>
          </div>
        ) : alert ? (
          <>
            {/* Step 1: Alert Detected */}
            <div className="p-6 border-b border-[var(--border-primary)]">
              <div className="flex items-center gap-2 mb-4">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500/20 text-[var(--accent-cyan)] text-xs font-bold">1</span>
                <h3 className="font-semibold text-[var(--text-primary)]">Alert Detected</h3>
              </div>
              <div className="flex items-start gap-4 mb-4">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                  isCritical ? 'bg-red-500/10' : isHigh ? 'bg-red-500/10' : 'bg-cyan-500/10'
                }`}>
                  <AlertTriangle className={`w-5 h-5 ${
                    isCritical || isHigh ? 'text-[var(--accent-red)]' : 'text-[var(--accent-cyan)]'
                  }`} />
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-[var(--text-primary)]">{alert.pathogen}</h2>
                  <p className="text-sm text-[var(--text-secondary)]">{alert.drugClass} Resistance Alert</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className={`pill text-xs ${isCritical || isHigh ? 'pill-red' : 'pill-cyan'}`}>
                  {severity} · Score: {alert.riskScore}/100
                </span>
                <span className="pill pill-slate text-xs">{alert.sector}</span>
                <span className="pill pill-slate text-xs capitalize">{alert.anomalyType?.replace('_', ' ')}</span>
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-[var(--text-muted)]">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{alert.subCounty}, {alert.county}</span>
                <span className="flex items-center gap-1"><FlaskConical className="w-3 h-3" />{alert.sector}</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(alert.triggeredAt).toLocaleString()}</span>
              </div>
            </div>

            {/* Step 2: AI Explanation */}
            {explanation && (
              <div className="p-6 border-b border-[var(--border-primary)]">
                <div className="flex items-center gap-2 mb-4">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-xs font-bold">2</span>
                  <h3 className="font-semibold text-[var(--text-primary)]">AI Explanation (SHAP)</h3>
                </div>
                <div className={`p-4 rounded-xl border mb-4 ${
                  isCritical || isHigh
                    ? 'bg-red-500/5 border-red-500/20'
                    : 'bg-cyan-500/5 border-cyan-500/20'
                }`}>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{explanation.plainTextSummary}</p>
                </div>
                {explanation.contributors?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 className="w-4 h-4 text-purple-400" />
                      <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Contributing Factors</span>
                    </div>
                    <div className="space-y-3">
                      {explanation.contributors.map((c, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between text-sm mb-1.5">
                            <span className="text-[var(--text-secondary)]">{c.factor}</span>
                            <span className="font-semibold text-[var(--text-primary)]">{c.contributionPercent}%</span>
                          </div>
                          <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-[var(--accent-cyan)] to-cyan-600 rounded-full"
                              style={{ width: `${c.contributionPercent}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Trend Chart (placed between explanation and actions for context) */}
            <div className="p-6 border-b border-[var(--border-primary)]">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-4 h-4 text-[var(--accent-red)]" />
                <h3 className="font-semibold text-[var(--text-primary)]">Resistance Trend</h3>
              </div>
              <TrendChart pathogen={alert.pathogen} drug={alert.drugClass} region={alert.subCounty} />
            </div>

            {/* Step 3: Recommended Actions */}
            {guidance && (guidance.recommendations?.length > 0 || guidance.actionChecklist?.length > 0) && (
              <div className="p-6 border-b border-[var(--border-primary)]">
                <div className="flex items-center gap-2 mb-4">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-teal-500/20 text-teal-400 text-xs font-bold">3</span>
                  <h3 className="font-semibold text-[var(--text-primary)]">Recommended Actions</h3>
                </div>
                {guidance.recommendations?.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">Recommendations</h4>
                    <ul className="space-y-2">
                      {guidance.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                          <CheckCircle2 className="w-4 h-4 text-[var(--accent-cyan)] flex-shrink-0 mt-0.5" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guidance.actionChecklist?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">Action Checklist</h4>
                    <ul className="space-y-2">
                      {guidance.actionChecklist.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-3 text-sm text-[var(--text-secondary)] p-2.5 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors">
                          <span className="w-6 h-6 rounded-full bg-cyan-500/10 text-[var(--accent-cyan)] text-xs font-bold flex items-center justify-center flex-shrink-0">
                            {idx + 1}
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guidance.references?.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-[var(--border-primary)]">
                    <h4 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">References</h4>
                    {guidance.references.map((ref, idx) => (
                      <a key={idx} href={ref.url} className="flex items-center gap-1 text-sm text-[var(--accent-cyan)] hover:underline">
                        <ExternalLink className="w-3 h-3" />{ref.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Step 4: Notification */}
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold">4</span>
                <h3 className="font-semibold text-[var(--text-primary)]">Notification</h3>
              </div>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                Dispatch SMS alert to {alert.county} County AMR Focal Person.
              </p>
              <button
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('sms-notification', { detail: alert }));
                  onClose();
                }}
                className="btn-primary flex items-center gap-2"
              >
                <Send className="w-4 h-4" /> Send SMS Notification
              </button>
            </div>
          </>
        ) : (
          <div className="text-center py-20 text-[var(--text-muted)]">Alert not found</div>
        )}
      </div>
    </div>
  );
}