import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { ShieldExclamationIcon, BeakerIcon, GlobeAmericasIcon } from '@heroicons/react/24/outline';

const SECTOR_COLORS = {
  human: '#ef4444',     // Red - Clinical pressure
  animal: '#f59e0b',    // Amber - Veterinary/Agricultural
  environment: '#10b981'// Emerald - Environmental reservoir
};

const SECTOR_METADATA = {
  human: {
    title: "Human Clinical Sector",
    insight: "Reflects direct therapeutic pressure and nosocomial spread. Spikes indicate broad-spectrum antibiotic overuse in inpatient wards."
  },
  animal: {
    title: "Animal & Livestock Sector",
    insight: "Driven by metaphylactic use and growth promotion. Elevated trends signal zoonotic spillover risks via the food chain."
  },
  environment: {
    title: "Environmental & Wastewater",
    insight: "Acts as a genetic melting pot. High scores indicate agricultural runoff or hospital effluent driving horizontal gene transfer."
  }
};

export default function SectorPieChart({ data, trendData = [] }) {
  const [activeTab, setActiveTab] = useState('trend'); // 'trend' or 'snapshot'

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6 flex flex-col gap-6">
      
      {/* Header & View Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">One Health MDR by Sector</h3>
          <p className="text-xs text-gray-500">Monthly evolution and cross-sector resistance dynamics</p>
        </div>
        <div className="flex bg-gray-100 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('trend')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'trend' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-900'}`}
          >
            Monthly Trend
          </button>
          <button
            onClick={() => setActiveTab('snapshot')}
            className={`px-3 py-1.5 rounded-lg transition ${activeTab === 'snapshot' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-900'}`}
          >
            Overall Snapshot
          </button>
        </div>
      </div>

      {/* Chart View */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={trendData.length > 0 ? trendData : data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} tickLine={false} />
            <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} unit="%" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
              formatter={(value, name) => [`${value}%`, `${name.toUpperCase()} Sector`]}
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            <Bar dataKey="human" name="Human Clinical" fill={SECTOR_COLORS.human} radius={[4, 4, 0, 0]} />
            <Bar dataKey="animal" name="Animal / Vet" fill={SECTOR_COLORS.animal} radius={[4, 4, 0, 0]} />
            <Bar dataKey="environment" name="Environment" fill={SECTOR_COLORS.environment} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Epidemiological Insight Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-gray-100">
        {Object.entries(SECTOR_METADATA).map(([key, meta]) => (
          <div key={key} className="bg-gray-50/70 p-3.5 rounded-xl border border-gray-100 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SECTOR_COLORS[key] }}></span>
                <h4 className="text-xs font-bold text-gray-800">{meta.title}</h4>
              </div>
              <p className="text-[11px] text-gray-600 leading-relaxed">{meta.insight}</p>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}