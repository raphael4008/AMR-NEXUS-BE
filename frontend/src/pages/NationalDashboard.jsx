/**
 * NationalDashboard.jsx — AMR-Nexus National Overview
 *
 * Design: matches existing app light theme (bg-white/80, text-gray-900, primary-600)
 * Data:   Promise.allSettled → safe .data unwrap → correct field mapping
 */

import { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts';
import api from '../api/client';

// ── Stat Card — light theme ──────────────────────────────────────────────────

function StatCard({ label, value, sub, accent = 'primary' }) {
  const accents = {
    primary: 'bg-primary-50 text-primary-700 border-primary-200',
    green:   'bg-green-50  text-green-700  border-green-200',
    amber:   'bg-amber-50  text-amber-700  border-amber-200',
    red:     'bg-red-50    text-red-700    border-red-200',
  };
  return (
    <div className={`rounded-2xl border p-5 flex flex-col gap-1 ${accents[accent]}`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

// ── Loading Skeleton ─────────────────────────────────────────────────────────

function Skeleton({ className = 'h-8 w-full' }) {
  return <div className={`animate-pulse bg-gray-100 rounded-xl ${className}`} />;
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function NationalDashboard() {
  const [summary,   setSummary]   = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [pathogens, setPathogens] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, trendRes, pathogenRes] = await Promise.allSettled([
          api.getSummary(),
          api.getMDRTrend(12),
          api.getByPathogen(10),
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

        if (pathogenRes.status === 'fulfilled') {
          const raw = pathogenRes.value.data?.data ?? pathogenRes.value.data ?? [];
          setPathogens((Array.isArray(raw) ? raw : []).map(p => ({
            name:       p.pathogen_name ?? p.name ?? 'Unknown',
            resistance: p.count ?? p.resistance ?? 0,
          })));
        }
      } catch (err) {
        console.error('[NationalDashboard]', err);
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    load();
    const interval = setInterval(load, 120_000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-500 text-center text-sm">{error}</p>
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
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-gray-900">National AMR Overview</h1>
        {summary?.last_updated && (
          <p className="text-xs text-gray-400">
            Updated: {new Date(summary.last_updated).toLocaleString()}
          </p>
        )}
      </div>

      {/* ── KPI Cards ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-2xl" />)
        ) : (
          <>
            <StatCard
              label="Total Isolates Scanned"
              value={(summary?.total_records ?? summary?.total_isolates_scanned)?.toLocaleString()}
              accent="primary"
            />
            <StatCard
              label="National MDR Rate"
              value={summary?.mdr_rate != null ? `${summary.mdr_rate.toFixed(1)}%` : '—'}
              sub="Multi-Drug Resistant"
              accent={summary?.mdr_rate > 30 ? 'red' : 'green'}
            />
            <StatCard
              label="Active Hotspots"
              value={summary?.active_hotspots ?? summary?.active_hotspots_detected ?? '—'}
              accent="amber"
            />
            <StatCard
              label="Active Counties"
              value={summary?.active_counties ?? '—'}
              accent="primary"
            />
          </>
        )}
      </div>

      {/* ── Charts Row ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* MDR Trend */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">MDR Resistance Trend (12 months)</h2>
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : trendData.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-12">No trend data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} unit="%" />
                <Tooltip
                  contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }}
                  formatter={v => [`${v}%`, 'Resistance Rate']}
                />
                <Line type="monotone" dataKey="rate" stroke="#2563eb" strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pathogens Bar */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Top Resistant Pathogens</h2>
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : pathogens.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-12">No pathogen data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={pathogens} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis dataKey="name" type="category" width={130} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip
                  contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }}
                  formatter={v => [v, 'Isolates']}
                />
                <Bar dataKey="resistance" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Recent Anomalies ────────────────────────────────────────────────── */}
      {summary?.recent_anomalies?.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-amber-200 p-5">
          <h2 className="text-sm font-semibold text-amber-700 mb-3">Recent Anomalies</h2>
          <div className="space-y-2">
            {summary.recent_anomalies.slice(0, 5).map((a, i) => (
              <div key={a.record_id ?? i} className="flex justify-between items-center text-sm text-gray-700 border-b border-gray-100 pb-2">
                <span>{a.pathogen_name} — {a.county}</span>
                <span className="text-amber-600 text-xs font-medium">Score: {a.anomaly_score?.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
