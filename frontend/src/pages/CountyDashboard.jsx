/**
 * CountyDashboard.jsx — AMR-Nexus County-Level Dashboard
 *
 * Design: matches original app light theme (bg-white/80, text-gray-900, primary-600)
 * Data:   Promise.allSettled → safe .data unwrap → correct field mapping
 */

import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import CountyHeatmap from '../components/analytics/CountyHeatmap';

// ── Stat Card — light theme ──────────────────────────────────────────────────

function Stat({ label, value, unit = '', accent = 'primary' }) {
  const accents = {
    primary: 'bg-primary-50 border-primary-200 text-primary-700',
    green:   'bg-green-50  border-green-200  text-green-700',
    amber:   'bg-amber-50  border-amber-200  text-amber-700',
    red:     'bg-red-50    border-red-200    text-red-700',
  }[accent] ?? 'bg-primary-50 border-primary-200 text-primary-700';

  return (
    <div className={`border rounded-2xl p-5 ${accent}`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold mt-1">
        {value ?? '—'}{unit}
      </p>
    </div>
  );
}

// ── Loading Skeleton ─────────────────────────────────────────────────────────

function Skeleton({ className = 'h-8 w-full rounded-xl' }) {
  return <div className={`animate-pulse bg-gray-100 ${className}`} />;
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function CountyDashboard() {
  const { user } = useAuth();
  const county = user?.county ?? 'Nairobi';

  const [summary,   setSummary]   = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [heatmap,   setHeatmap]   = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    if (!county) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, trendRes, heatmapRes] = await Promise.allSettled([
          api.getSummary({ county }),
          api.getMDRTrend(12, { county }),
          api.getHeatmapCoordinates({ county, limit: 500 }),
        ]);

        if (summaryRes.status === 'fulfilled') {
          setSummary(summaryRes.value.data ?? null);
        }

        if (trendRes.status === 'fulfilled') {
          const raw = trendRes.value.data?.series ?? [];
          setTrendData(raw.map(pt => ({
            month: pt.date?.slice(0, 7) ?? '',
            rate:  parseFloat(((pt.resistance_rate ?? 0) * 100).toFixed(1)),
          })));
        }

        if (heatmapRes.status === 'fulfilled') {
          const raw = heatmapRes.value.data;
          setHeatmap(Array.isArray(raw) ? raw : []);
        }
      } catch (err) {
        console.error('[CountyDashboard]', err);
        setError('Failed to load county data.');
      } finally {
        setLoading(false);
      }
    };

    load();
    const interval = setInterval(load, 120_000);
    return () => clearInterval(interval);
  }, [county]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-500 text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary-600 text-white rounded-full text-sm hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{county} County Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          AMR surveillance data for {county} County · Kenya One Health
        </p>
      </div>

      {/* ── KPI Cards ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-2xl" />)
        ) : (
          <>
            <Stat
              label="Total Records"
              value={summary?.total_records?.toLocaleString()}
              accent="primary"
            />
            <Stat
              label="MDR Rate"
              value={summary?.mdr_rate != null ? summary.mdr_rate.toFixed(1) : '—'}
              unit="%"
              accent={summary?.mdr_rate > 30 ? 'red' : 'green'}
            />
            <Stat
              label="Anomalies"
              value={summary?.anomaly_count ?? '—'}
              accent="amber"
            />
            <Stat
              label="Active Hotspots"
              value={summary?.active_hotspots ?? summary?.active_hotspots_detected ?? '—'}
              accent="red"
            />
          </>
        )}
      </div>

      {/* ── Trend Chart ────────────────────────────────────────────────────── */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          MDR Resistance Trend — {county} (12 months)
        </h2>
        {loading ? (
          <Skeleton className="h-48 rounded-xl" />
        ) : trendData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-12">No trend data for {county}</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }}
                formatter={v => [`${v}%`, 'MDR Rate']}
              />
              <Line type="monotone" dataKey="rate" stroke="#2563eb" strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Heatmap ────────────────────────────────────────────────────────── */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Resistance Heatmap — {county}</h2>
        </div>
        {loading ? (
          <Skeleton className="h-64 rounded-none" />
        ) : (
          <CountyHeatmap data={heatmap} county={county} />
        )}
      </div>

    </div>
  );
}
