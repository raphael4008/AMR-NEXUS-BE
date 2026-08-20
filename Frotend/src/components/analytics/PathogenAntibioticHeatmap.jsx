// src/components/analytics/PathogenAntibioticHeatmap.jsx (fixed to handle errors)
import { useEffect, useState } from 'react';
import api from '../../api/client';

export default function PathogenAntibioticHeatmap({ startDate, endDate, county }) {
  const [matrix, setMatrix] = useState({ pathogens: [], antibiotics: [], data: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMatrix = async () => {
      setLoading(true);
      setError(null);
      try {
        const pathogens = await api.getByPathogen(20);
        const pathogenCodes = pathogens.map(p => p.name);
        const antibiotics = ['Fluoroquinolone', 'Penicillin', 'Carbapenem', 'Tetracycline', 'Cephalosporin'];
        const data = {};
        for (const code of pathogenCodes) {
          try {
            const res = await fetch(`http://localhost:8000/analytics/resistance_by_pathogen/${code}?${new URLSearchParams({ start_date: startDate, end_date: endDate, county })}`);
            if (!res.ok) {
              data[code] = [];
              continue;
            }
            const classData = await res.json();
            data[code] = Array.isArray(classData) ? classData : [];
          } catch (e) {
            data[code] = [];
          }
        }
        setMatrix({ pathogens: pathogenCodes, antibiotics, data });
      } catch (err) {
        console.error(err);
        setError('Failed to load pathogen-antibiotic matrix');
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
    return 'bg-green-500 text-white';
  };

  if (loading) return <div className="text-center p-4">Loading matrix...</div>;
  if (error) return <div className="text-center text-red-500 p-4">{error}</div>;
  if (matrix.pathogens.length === 0) return <div className="text-center p-4">No pathogen data available</div>;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 overflow-x-auto">
      <h3 className="text-md font-semibold mb-2">Pathogen vs Antibiotic Class Resistance (%)</h3>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th className="px-2 py-1">Pathogen</th>
            {matrix.antibiotics.map(ab => (
              <th key={ab} className="px-2 py-1">{ab}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.pathogens.map(path => {
            const rowData = matrix.data[path] || [];
            return (
              <tr key={path}>
                <td className="font-mono">{path}</td>
                {matrix.antibiotics.map(ab => {
                  const val = rowData.find(c => c.antibiotic_class === ab)?.resistance || 0;
                  return <td key={ab} className={`p-1 text-center ${getCellColor(val)}`}>{val.toFixed(0)}%</td>;
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}