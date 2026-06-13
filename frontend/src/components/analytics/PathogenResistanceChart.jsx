import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';

export default function PathogenResistanceChart({ data, onDrillDown }) {
  const navigate = useNavigate();
  const safeData = Array.isArray(data) ? data : [];

  const handleClick = (pathogen) => {
    if (onDrillDown) onDrillDown(pathogen);
    else navigate(`/pathogen-explorer?pathogen=${pathogen}`);
  };

  if (safeData.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold mb-2 text-gray-800">Resistance by Pathogen</h3>
        <p className="text-gray-400 text-center py-8">No pathogen data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold mb-2 text-gray-800">Resistance by Pathogen (click bar to explore)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={safeData} layout="vertical" margin={{ left: 40 }} onClick={(e) => e && e.activePayload && handleClick(e.activePayload[0].payload.name)}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 100]} unit="%" />
          <YAxis type="category" dataKey="name" width={80} />
          <Tooltip formatter={(v) => `${v}%`} />
          <Bar dataKey="resistance" fill="#10b981" name="Resistance (%)" cursor="pointer" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}