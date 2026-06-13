import { useEffect, useState } from 'react';
import api from '../../api/client';

export default function PathogenAntibioticHeatmap({ startDate, endDate, county }) {
  const [matrix, setMatrix] = useState({ pathogens: [], antibiotics: [], data: {} });

  useEffect(() => {
    const fetchMatrix = async () => {
      try {
        const pathogens = await api.getByPathogen(20);
        const pathogenCodes = pathogens.map(p => p.name).filter(Boolean);
        const antibiotics = ['Fluoroquinolone', 'Penicillin', 'Carbapenem', 'Tetracycline', 'Cephalosporin'];

        // Fetch heatmap once, then slice per pathogen (avoid N+1 requests)
        const heatmapData = await api.getHeatmap({ limit: 2000 });

        const cellData = {};
        for (const code of pathogenCodes) {
          const rows = heatmapData.filter(
            r => (r.pathogen_profile ?? '').toLowerCase() === code.toLowerCase()
          );
          cellData[code] = rows.map(r => ({
            antibiotic_class: r.antibiotic_name ?? 'Unknown',
            resistance: (r.intensity_weight ?? 0) * 100,
          }));
        }
        setMatrix({ pathogens: pathogenCodes, antibiotics, data: cellData });
      } catch (err) {
        console.error('PathogenAntibioticHeatmap error:', err);
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

  if (!matrix.pathogens.length) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold mb-2">Pathogen vs Antibiotic Class Resistance (%)</h3>
        <p className="text-gray-400 text-center py-8">No cross-resistance data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 overflow-x-auto">
      <h3 className="text-md font-semibold mb-2">Pathogen vs Antibiotic Class Resistance (%)</h3>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th className="text-left px-2 py-1">Pathogen</th>
            {matrix.antibiotics.map(ab => <th key={ab} className="px-2 py-1">{ab}</th>)}
          </tr>
        </thead>
        <tbody>
          {matrix.pathogens.map(path => (
            <tr key={path}>
              <td className="font-mono px-2 py-1">{path}</td>
              {matrix.antibiotics.map(ab => {
                const val = matrix.data[path]?.find(c => c.antibiotic_class === ab)?.resistance ?? 0;
                return (
                  <td key={ab} className={`p-1 text-center ${getCellColor(val)}`}>
                    {val.toFixed(0)}%
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}