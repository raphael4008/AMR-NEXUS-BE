import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function SectorPieChart({ data }) {
  const safeData = Array.isArray(data) ? data : [];

  if (safeData.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold mb-2 text-gray-800">MDR by Sector</h3>
        <p className="text-gray-400 text-center py-8">No sector data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold mb-2 text-gray-800">MDR by Sector</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={safeData}
            cx="50%"
            cy="50%"
            outerRadius={80}
            dataKey="value"
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          >
            {safeData.map((entry, idx) => (
              <Cell key={entry.name ?? idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `${v}%`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}