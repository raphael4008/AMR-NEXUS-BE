import { useEffect, useState } from 'react';
import api from '../../api/client';

/**
 * PathogenAntibioticHeatmap — Pathogen × Antibiotic Class resistance grid
 *
 * Derives data from api.getPredictions() — groups by (pathogen, antibiotic_class)
 * and calculates resistance % in the browser. No localhost:8000 fetch needed.
 */
export default function PathogenAntibioticHeatmap({ startDate, endDate, county }) {
  const [matrix, setMatrix] = useState({ pathogens: [], antibiotics: [], data: {} });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchMatrix = async () => {
      setLoading(true);
      try {
        const params = {};
        if (startDate) params.start_date = startDate;
        if (endDate)   params.end_date   = endDate;
        if (county)    params.county     = county;

        const res = await api.getPredictions(2000, 0, params);
        const records = Array.isArray(res.data) ? res.data : [];

        // Aggregate resistance: { pathogen → { antibiotic_class → { total, resistant } } }
        const agg = {};
        records.forEach(r => {
          const path = r.pathogen_name ?? r.pathogen_code ?? 'Unknown';
          const cls  = r.antibiotic_class ?? r.antibiotic_name ?? 'Unknown';
          if (!agg[path]) agg[path] = {};
          if (!agg[path][cls]) agg[path][cls] = { total: 0, resistant: 0 };
          agg[path][cls].total++;
          if (r.mdr_flag || r.sir_result === 'R') agg[path][cls].resistant++;
        });

        // Top 8 pathogens by record count
        const pathogenList = Object.entries(agg)
          .sort(([, a], [, b]) => {
            const sumA = Object.values(a).reduce((s, v) => s + v.total, 0);
            const sumB = Object.values(b).reduce((s, v) => s + v.total, 0);
            return sumB - sumA;
          })
          .slice(0, 8)
          .map(([name]) => name);

        // All antibiotic classes seen
        const antibioticSet = new Set();
        pathogenList.forEach(p => Object.keys(agg[p] ?? {}).forEach(k => antibioticSet.add(k)));
        const antibioticList = [...antibioticSet].sort().slice(0, 8);

        // Build data map: { pathogen → { antibiotic → resistance% } }
        const dataMap = {};
        pathogenList.forEach(p => {
          dataMap[p] = {};
          antibioticList.forEach(ab => {
            const cell = agg[p]?.[ab];
            dataMap[p][ab] = cell && cell.total > 0
              ? parseFloat((cell.resistant / cell.total * 100).toFixed(1))
              : 0;
          });
        });

        setMatrix({ pathogens: pathogenList, antibiotics: antibioticList, data: dataMap });
      } catch (err) {
        console.error('[PathogenAntibioticHeatmap]', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMatrix();
  }, [startDate, endDate, county]);

  const getCellColor = (resistance) => {
    if (resistance > 60) return 'bg-red-600 text-white';
    if (resistance > 40) return 'bg-orange-500 text-white';
    if (resistance > 20) return 'bg-yellow-400 text-black';
    if (resistance > 0)  return 'bg-green-500 text-white';
    return 'bg-gray-100 text-gray-400';
  };

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold mb-2">Pathogen vs Antibiotic Class Resistance (%)</h3>
        <div className="animate-pulse bg-gray-100 rounded-xl h-48 w-full" />
      </div>
    );
  }

  if (matrix.pathogens.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold mb-2">Pathogen vs Antibiotic Class Resistance (%)</h3>
        <p className="text-gray-400 text-sm text-center py-8">No resistance data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 overflow-x-auto">
      <h3 className="text-md font-semibold mb-3 text-gray-800">Pathogen vs Antibiotic Class Resistance (%)</h3>
      <table className="min-w-full text-xs border-separate border-spacing-0.5">
        <thead>
          <tr>
            <th className="text-left px-2 py-1 text-gray-600 font-semibold">Pathogen</th>
            {matrix.antibiotics.map(ab => (
              <th key={ab} className="px-2 py-1 text-gray-600 font-semibold whitespace-nowrap">{ab}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.pathogens.map(path => (
            <tr key={path}>
              <td className="font-mono px-2 py-1 text-gray-700 whitespace-nowrap text-xs">{path}</td>
              {matrix.antibiotics.map(ab => {
                const val = matrix.data[path]?.[ab] ?? 0;
                return (
                  <td key={ab} className={`px-2 py-1 text-center rounded ${getCellColor(val)}`}>
                    {val > 0 ? `${val.toFixed(0)}%` : '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex gap-4 mt-3 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-600 inline-block"/>{'>'} 60%</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-orange-500 inline-block"/>41–60%</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-400 inline-block"/>21–40%</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500 inline-block"/>≤ 20%</span>
      </div>
    </div>
  );
}