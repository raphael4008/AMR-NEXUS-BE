import { AlertTriangle, TrendingUp } from 'lucide-react';
import { DataCard } from '../ui/DataCard';

export default function CountyTrendChart() {
  const trendData = [18, 19, 20, 22, 23, 28, 32, 34];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-glass)] rounded-[24px] p-5 shadow-lg transition-all hover:shadow-xl">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-9 h-9 rounded-xl bg-red-500/10 flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-red-500" strokeWidth={1.5} />
        </div>
        <div>
          <h3 className="font-semibold text-[13px] text-[var(--text-primary)]">
            Resistance Trend
          </h3>
          <p className="text-[11px] text-[var(--text-muted)]">
            Fluoroquinolone · E. coli · Ruiru Sub-County
          </p>
        </div>
      </div>

      {/* Chart */}
      <svg width="100%" height="180" viewBox="0 0 600 180" preserveAspectRatio="none" className="mb-2">
        <defs>
          <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.01" />
          </linearGradient>
          <linearGradient id="trendGradLight" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0066CC" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#0066CC" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        
        {/* Grid lines - theme aware */}
        {[0, 25, 50, 75, 100].map((pct) => (
          <line
            key={pct}
            x1="0"
            y1={pct}
            x2="600"
            y2={pct}
            stroke="var(--border-default)"
            strokeWidth="0.5"
            strokeDasharray="4 4"
            opacity={0.3}
          />
        ))}
        
        {(() => {
          const max = Math.max(...trendData);
          const min = Math.min(...trendData);
          const range = max - min || 1;
          const padding = 25;
          const chartWidth = 600;
          const chartHeight = 180;
          const plotHeight = chartHeight - padding * 2;
          const stepX = chartWidth / (trendData.length - 1);

          const points = trendData
            .map((v, i) => `${i * stepX},${padding + ((max - v) / range) * plotHeight}`)
            .join(' ');

          const firstY = padding + ((max - trendData[0]) / range) * plotHeight;
          const lastX = (trendData.length - 1) * stepX;
          const lastY = padding + ((max - trendData[trendData.length - 1]) / range) * plotHeight;
          const areaPoints = `0,${chartHeight} 0,${firstY} ${points} ${lastX},${lastY} ${lastX},${chartHeight}`;

          // Anomaly points (indices 5, 6, 7)
          const anomalyIndices = [5, 6, 7];

          return (
            <>
              {/* Area fill */}
              <polygon points={areaPoints} fill="url(#trendGrad)" />
              
              {/* Line */}
              <polyline
                points={points}
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Dots for each point */}
              {trendData.map((v, i) => {
                const x = i * stepX;
                const y = padding + ((max - v) / range) * plotHeight;
                const isAnomaly = anomalyIndices.includes(i);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={isAnomaly ? "5" : "3.5"}
                    fill={isAnomaly ? "#EF4444" : "var(--accent)"}
                    stroke="var(--bg-card)"
                    strokeWidth="2"
                    className="transition-all duration-300"
                  />
                );
              })}

              {/* Anomaly highlight zones */}
              {anomalyIndices.map((i) => {
                const x = i * stepX;
                const y = padding + ((max - trendData[i]) / range) * plotHeight;
                return (
                  <circle
                    key={`pulse-${i}`}
                    cx={x}
                    cy={y}
                    r="14"
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="1.5"
                    opacity="0.4"
                    className="animate-pulse"
                  />
                );
              })}
            </>
          );
        })()}
      </svg>

      {/* Month Labels */}
      <div className="flex justify-between px-1 mb-5">
        {months.map((m, i) => (
          <span
            key={i}
            className={`text-[10px] font-medium transition-colors ${
              i >= 5
                ? 'text-red-500 font-semibold'
                : 'text-[var(--text-muted)]'
            }`}
          >
            {m}
          </span>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-5 text-[10px]">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 rounded-full bg-[var(--accent)]" />
          <span className="text-[var(--text-muted)]">Resistance Rate</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-[var(--text-muted)]">Anomaly Detected</span>
        </div>
      </div>

      {/* Anomaly Alert */}
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex gap-3 transition-all hover:bg-red-500/15">
        <div className="w-8 h-8 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
          <AlertTriangle className="w-4 h-4 text-red-500" strokeWidth={1.5} />
        </div>
        <div>
          <p className="text-[13px] font-semibold text-red-600 dark:text-red-400">
            Anomaly Detected — Sharp Resistance Increase
          </p>
          <p className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">
            Fluoroquinolone resistance in poultry E. coli rose from 22% to 34% in the last 3 months. 
            This correlates with high antibiotic usage in poultry feed and imported day-old chicks from unregulated sources.
          </p>
          <div className="flex gap-2 mt-3 flex-wrap">
            {['Jul: 32%', 'Aug: 34%'].map((point) => (
              <span key={point} className="px-2 py-0.5 rounded-full text-[9px] font-semibold uppercase tracking-wider bg-red-500/10 text-red-500 border border-red-500/20">
                {point}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
