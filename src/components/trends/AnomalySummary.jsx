import { AlertTriangle, MapPin, TrendingUp, ChevronRight } from 'lucide-react';

export default function AnomalySummary({ anomalies = [], onAnomalyClick }) {
  const data = anomalies.length > 0 ? anomalies : [
    { id: 'ALT-001', pathogen: 'K. pneumoniae', drug: 'Carbapenem', county: 'Nairobi', riskScore: 89, detectedAt: '2h ago' },
    { id: 'ALT-002', pathogen: 'E. coli', drug: 'ESBL', county: 'Mombasa', riskScore: 95, detectedAt: '5h ago' },
    { id: 'ALT-003', pathogen: 'E. coli', drug: 'Fluoroquinolone', county: 'Kiambu', riskScore: 78, detectedAt: '1d ago' },
  ];

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border-primary)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-red-500/10 flex items-center justify-center">
            <TrendingUp className="w-3.5 h-3.5 text-[var(--accent-red)]" />
          </div>
          <span className="section-label">Anomaly Summary</span>
        </div>
        <span className="pill pill-red text-[10px]">{data.length} active</span>
      </div>

      {/* List */}
      <div className="divide-y divide-[var(--border-primary)] max-h-[400px] overflow-y-auto">
        {data.map((a, idx) => {
          const isCritical = a.riskScore >= 90;
          const isHigh = a.riskScore >= 75 && a.riskScore < 90;

          return (
            <button
              key={a.id}
              onClick={() => onAnomalyClick?.(a)}
              className="w-full text-left p-3.5 hover:bg-[var(--bg-tertiary)] transition-colors group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[12px] font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-cyan)] transition-colors">
                  {a.pathogen}
                </span>
                <span className={`pill text-[10px] ${isCritical ? 'pill-red' : isHigh ? 'pill-red' : 'pill-cyan'}`}>
                  {a.riskScore}
                </span>
              </div>

              <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)] mb-1">
                <span className="font-medium text-[var(--text-secondary)]">{a.drug}</span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-2.5 h-2.5" />
                  {a.county}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="flex items-center gap-1 text-[var(--accent-red)] font-medium">
                    <TrendingUp className="w-2.5 h-2.5" />
                    Rising
                  </span>
                  <span className="text-[var(--text-muted)]">{a.detectedAt}</span>
                </div>
                <ChevronRight className="w-3 h-3 text-[var(--text-muted)] group-hover:text-[var(--accent-cyan)] transition-colors" />
              </div>

              {/* Risk bar */}
              <div className="mt-2 h-1 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isCritical ? 'bg-[var(--accent-red)]' : isHigh ? 'bg-orange-500' : 'bg-[var(--accent-cyan)]'
                  }`}
                  style={{ width: `${a.riskScore}%` }}
                />
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer */}
      {data.length > 0 && (
        <div className="px-4 py-2.5 border-t border-[var(--border-primary)]">
          <button className="w-full text-[11px] font-medium text-[var(--accent-cyan)] hover:opacity-80 transition-opacity text-center">
            View all anomalies →
          </button>
        </div>
      )}
    </div>
  );
}