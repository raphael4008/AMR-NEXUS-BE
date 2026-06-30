import { useEffect, useState } from 'react';
import { ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import api from '../api/client';

export default function DataQuality() {
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    // Backend has no dedicated /data_quality endpoint.
    // Derive quality metrics from /analytics/summary + /predictions.
    const load = async () => {
      setLoading(true);
      try {
        const [summRes, predRes] = await Promise.allSettled([
          api.getSummary(),
          api.getPredictions(1000, 0),
        ]);

        const summ  = summRes.status  === 'fulfilled' ? (summRes.value.data  ?? {}) : {};
        const preds = predRes.status  === 'fulfilled' ? (Array.isArray(predRes.value.data) ? predRes.value.data : []) : [];

        const total = preds.length || summ.total_records || 0;
        const missingPathogen = preds.filter(p => !p.pathogen_name && !p.pathogen_code).length;
        const missingCounty   = preds.filter(p => !p.county).length;
        const withQuality     = preds.filter(p => p.data_quality_score != null);
        const avgQuality      = withQuality.length
          ? withQuality.reduce((s, p) => s + p.data_quality_score, 0) / withQuality.length
          : (summ.compliance_index ?? 0.85);

        setQuality({
          total_records:        total,
          missing_pathogen:     missingPathogen,
          missing_county:       missingCounty,
          completeness_percent: parseFloat((avgQuality * 100).toFixed(1)),
          mdr_rate:             summ.mdr_rate ?? null,
          anomaly_count:        summ.anomaly_count ?? null,
          active_counties:      summ.active_counties ?? null,
        });
      } catch (err) {
        console.error('[DataQuality]', err);
        setError('Failed to load data quality metrics.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
    </div>
  );

  if (error) return (
    <div className="text-center text-red-500 text-sm p-8">{error}</div>
  );

  if (!quality) return null;

  const isGood = quality.completeness_percent >= 85;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <ChartBarIcon className="h-7 w-7 text-primary-600" />
        <h1 className="text-2xl font-bold text-gray-900">Data Quality Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Total Records</p>
          <p className="text-3xl font-bold text-gray-900">{quality.total_records?.toLocaleString() ?? '—'}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-yellow-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Missing Pathogen</p>
          <p className="text-3xl font-bold text-yellow-600">{quality.missing_pathogen ?? '—'}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-yellow-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Missing County</p>
          <p className="text-3xl font-bold text-yellow-600">{quality.missing_county ?? '—'}</p>
        </div>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            {isGood
              ? <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse inline-block" />
              : <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />
            }
            <h2 className="font-semibold text-gray-800">Completeness Score</h2>
          </div>
          <span className={`text-2xl font-bold ${isGood ? 'text-green-600' : 'text-amber-600'}`}>
            {quality.completeness_percent}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${isGood ? 'bg-green-500' : 'bg-amber-500'}`}
            style={{ width: `${quality.completeness_percent}%` }}
          />
        </div>
        <p className="text-xs text-gray-400">
          Target: ≥ 85% · Current: {quality.completeness_percent}% · {isGood ? '✅ Meets target' : '⚠️ Below target'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">National MDR Rate</p>
          <p className="text-2xl font-bold text-gray-900">{quality.mdr_rate != null ? `${quality.mdr_rate.toFixed(1)}%` : '—'}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Anomaly Count</p>
          <p className="text-2xl font-bold text-amber-600">{quality.anomaly_count ?? '—'}</p>
        </div>
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Active Counties</p>
          <p className="text-2xl font-bold text-gray-900">{quality.active_counties ?? '—'}</p>
        </div>
      </div>
    </div>
  );
}
