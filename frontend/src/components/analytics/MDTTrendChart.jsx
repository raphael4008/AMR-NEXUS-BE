/**
 * MDTTrendChart.jsx — AMR-Nexus MDR Trend Chart v2.2
 *
 * Bugs fixed:
 *  1. api.getForecast() DOES NOT EXIST — removed. Forecast is now fetched via
 *     api.getMDRTrend(12, { forecast: true }) using the ?forecast=true param.
 *  2. trendData initialised to [] (was undefined) preventing .slice() crash.
 *  3. Field names fixed: date→month, resistance_rate→rate.
 *  4. Forecast flag from series item used to style dashed forecast line.
 *
 * Props:
 *  county  - Optional county filter. If falsy, shows national trend.
 *  months  - Number of months to show (default 12).
 *  height  - Chart height (default 250).
 */

import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts';
import api from '../../api/client';

// ── Custom Tooltip ────────────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3 text-xs shadow-lg">
      <p className="text-gray-500 mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: <strong>{entry.value?.toFixed(1)}%</strong>
          {entry.payload?.forecast && ' (forecast)'}
        </p>
      ))}
    </div>
  );
};

// ── Main Component ─────────────────────────────────────────────────────────────

export default function MDTTrendChart({
  county   = null,
  months   = 12,
  height   = 250,
  showForecast = false,
}) {
  const [data,    setData]    = useState([]);   // Safe default []
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = {};
        if (county)       params.county   = county;
        if (showForecast) params.forecast = 'true';

        // FIX: Use getMDRTrend with forecast param — NOT the non-existent getForecast()
        const res = await api.getMDRTrend(months, params);

        // FIX: Unwrap { series: [...] } and remap field names
        const raw = res.data?.series ?? [];
        const mapped = raw.map((pt) => ({
          month:    pt.date?.slice(0, 7) ?? '',
          rate:     parseFloat((pt.resistance_rate * 100).toFixed(1)),
          forecast: Boolean(pt.forecast),
        }));
        setData(mapped);
      } catch (err) {
        console.error('[MDTTrendChart]', err);
        setError('Could not load trend data.');
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [county, months, showForecast]);

  // Split into actual vs forecast for styling
  const actual   = data.filter((d) => !d.forecast);
  const forecast = data.filter((d) => d.forecast);
  const splitAt  = actual.length > 0 ? actual[actual.length - 1]?.month : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="animate-pulse bg-white/10 rounded-xl w-full" style={{ height: height - 20 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center text-red-400 text-sm" style={{ height }}>
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-gray-400 text-sm" style={{ height }}>
        No trend data available{county ? ` for ${county}` : ''}
      </div>
    );
  }

  return (
    <div>
      {county && (
        <p className="text-xs text-slate-400 mb-2">County: <strong className="text-slate-200">{county}</strong></p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickFormatter={(v) => v.slice(5)}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#6b7280' }}
            unit="%"
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#6b7280' }}
          />

          {/* Split line at forecast boundary */}
          {splitAt && showForecast && (
            <ReferenceLine x={splitAt} stroke="#ffffff30" strokeDasharray="4 4" label={{ value: 'Forecast', fill: '#94a3b8', fontSize: 10 }} />
          )}

          {/* Actual data line */}
          <Line
            type="monotone"
            dataKey="rate"
            name="MDR Rate"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#3b82f6' }}
            connectNulls
          />

          {/* Forecast dashed overlay (if forecast data exists) */}
          {showForecast && forecast.length > 0 && (
            <Line
              type="monotone"
              dataKey="rate"
              name="Forecast"
              data={forecast}
              stroke="#06b6d4"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 5, fill: '#06b6d4' }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}