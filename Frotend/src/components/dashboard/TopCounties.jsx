// src/components/dashboard/TopCounties.jsx
import { MapPinIcon } from '@heroicons/react/24/outline';

export default function TopCounties({ counties }) {
  if (!counties || counties.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
        <h3 className="text-md font-semibold text-gray-800 mb-2">Top Counties by MDR Rate</h3>
        <p className="text-gray-500 text-center py-8">No county data</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-md font-semibold text-gray-800 mb-2 flex items-center gap-2">
        <MapPinIcon className="h-5 w-5 text-primary-500" /> Top Counties by MDR Rate
      </h3>
      <div className="space-y-3">
        {counties.map((item, idx) => (
          <div key={item.county}>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span className="font-medium">{idx + 1}. {item.county}</span>
              <span className="font-bold text-primary-600">{item.rate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div className="bg-primary-500 h-1.5 rounded-full" style={{ width: `${item.rate}%` }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}