import { useRef, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { AlertTriangle, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import { fetchTrends } from '../../api/endpoints';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div
        className="card p-3 !shadow-lg"
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}
      >
        <p className="text-xs text-[var(--text-muted)] mb-1">{label}</p>
        <p className="text-sm font-bold text-[var(--text-primary)]">
          Resistance: <span className="text-[var(--accent-red)]">{(data.resistanceRate * 100).toFixed(1)}%</span>
        </p>
        {data.anomalyFlag && (
          <div className="flex items-center gap-1 text-[var(--accent-red)] text-xs font-semibold mt-1">
            <AlertTriangle className="w-3 h-3" />
            Anomaly Detected
          </div>
        )}
      </div>
    );
  }
  return null;
};

export default function TrendChart({
  pathogen = 'Klebsiella pneumoniae',
  drug = 'Carbapenem',
  region = 'Nairobi',
  months = 12,
}) {
  const containerRef = useRef(null);
  const [ready, setReady] = useState(false);

  // Wait until the container has real dimensions
  useEffect(() => {
    const check = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        if (width > 0 && height > 0) {
          setReady(true);
        } else {
          setReady(false);
        }
      }
    };
    check();
    const timer = setInterval(check, 50); // keep checking until ready
    window.addEventListener('resize', check);
    return () => {
      clearInterval(timer);
      window.removeEventListener('resize', check);
    };
  }, []);

  const { data, isLoading, error } = useQuery({
    queryKey: ['trends', pathogen, drug, region, months],
    queryFn: fetchTrends,
  });

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-[var(--accent-cyan)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card flex items-center justify-center h-64 text-[var(--accent-red)] gap-2">
        <AlertTriangle className="w-5 h-5" />
        <span className="text-sm">Failed to load trend data</span>
      </div>
    );
  }

  const series = data?.series || [];
  const anomalyPoints = series.filter(d => d.anomalyFlag);
  const hasAnomaly = anomalyPoints.length > 0;
  const trendUp = series.length > 1 && series[series.length - 1].resistanceRate > series[0].resistanceRate;

  return (
    <div className="card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              trendUp ? 'bg-red-500/10' : 'bg-cyan-500/10'
            }`}
          >
            {trendUp ? (
              <TrendingUp className="w-5 h-5 text-[var(--accent-red)]" />
            ) : (
              <TrendingDown className="w-5 h-5 text-[var(--accent-cyan)]" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-base text-[var(--text-primary)]">{pathogen}</h3>
            <p className="text-sm text-[var(--text-secondary)]">
              {drug} Resistance · {region} · {months} months
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {hasAnomaly && (
            <span className="pill pill-red text-[10px] flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {anomalyPoints.length} Anomal{anomalyPoints.length > 1 ? 'ies' : 'y'}
            </span>
          )}
          <span className={`pill text-[10px] ${trendUp ? 'pill-red' : 'pill-cyan'}`}>
            {trendUp ? '↑ Rising' : '↓ Falling'}
          </span>
        </div>
      </div>

      {/* Chart container – always has min height, but chart mounts only when ready */}
      <div
        ref={containerRef}
        className="h-72 min-h-[200px] w-full relative"
      >
        {!ready && (
          <div className="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-sm">
            Loading chart…
          </div>
        )}
        {ready && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={series} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="resistanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" strokeOpacity={0.5} vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
              />
              <YAxis
                tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                domain={[0, 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={0.25}
                stroke="var(--accent-red)"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{ value: 'Threshold 25%', fill: 'var(--accent-red)', fontSize: 11, position: 'right' }}
              />
              <Area type="monotone" dataKey="resistanceRate" fill="url(#resistanceGradient)" stroke="none" />
              <Line
                type="monotone"
                dataKey="resistanceRate"
                stroke="var(--accent-cyan)"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, fill: 'var(--accent-cyan)', stroke: 'var(--bg-primary)', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Anomaly Details */}
      {hasAnomaly && (
        <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-[var(--accent-red)] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-[var(--accent-red)]">
              Anomaly Detected — Significant Resistance Spike
            </p>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Resistance rate increased sharply in the last {anomalyPoints.length} month{anomalyPoints.length > 1 ? 's' : ''},
              exceeding the 25% threshold.
            </p>
            <div className="flex gap-2 mt-3 flex-wrap">
              {anomalyPoints.map((point, idx) => (
                <span key={idx} className="pill pill-red text-[10px]">
                  {new Date(point.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}: {(point.resistanceRate * 100).toFixed(1)}%
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}