import { useEffect, useState } from 'react';

export function KPICard({ label, value, icon: Icon, change, changeType = 'up', sparkline }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const duration = 1000, steps = 40, increment = value / steps;
    let current = 0, step = 0;
    const interval = setInterval(() => {
      step++; current += increment;
      if (step >= steps) { setDisplayValue(value); clearInterval(interval); }
      else setDisplayValue(Math.floor(current));
    }, duration / steps);
    return () => clearInterval(interval);
  }, [value]);

  const changeColor = changeType === 'up' ? 'var(--accent-cyan)' : 'var(--accent-red)';
  const changeBg = changeType === 'up' ? 'rgba(8,145,178,0.1)' : 'rgba(220,38,38,0.1)';

  return (
    <div className="card p-5 transition-all duration-200 hover:border-[var(--accent-cyan)]/50">
      <div className="flex items-center justify-between mb-4">
        <span className="section-label">{label}</span>
        <div className="w-9 h-9 rounded-xl bg-[var(--bg-tertiary)] flex items-center justify-center">
          <Icon className="w-4 h-4 text-[var(--accent-cyan)]" />
        </div>
      </div>

      <div className="flex items-baseline gap-3 mb-3">
        <span className="data-number text-[42px]">{displayValue.toLocaleString()}</span>
        {change && (
          <span
            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold"
            style={{ color: changeColor, backgroundColor: changeBg }}
          >
            {changeType === 'up' ? '↑' : '↓'} {change}%
          </span>
        )}
      </div>

      {sparkline && (
        <div className="flex items-end gap-1 h-8">
          {sparkline.map((val, idx) => {
            const max = Math.max(...sparkline);
            return (
              <div
                key={idx}
                className="flex-1 rounded-sm bg-[var(--accent-cyan)]/50"
                style={{ height: `${(val / max) * 100}%`, minHeight: 3 }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}