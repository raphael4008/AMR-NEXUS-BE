import { Bug, User, Leaf, Link2 } from 'lucide-react';

export default function OneHealthOverlap() {
  const sectors = [
    { icon: User, label: 'Human', count: 412, color: 'from-blue-500 to-indigo-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30', textColor: 'text-blue-600 dark:text-blue-400' },
    { icon: Bug, label: 'Animal', count: 115, color: 'from-amber-500 to-orange-600', bgColor: 'bg-amber-100 dark:bg-amber-900/30', textColor: 'text-amber-600 dark:text-amber-400' },
    { icon: Leaf, label: 'Environment', count: 28, color: 'from-green-500 to-emerald-600', bgColor: 'bg-green-100 dark:bg-green-900/30', textColor: 'text-green-600 dark:text-green-400' },
  ];

  const overlaps = [
    { from: 'Human', to: 'Animal', count: 3, resistance: 'Carbapenem' },
    { from: 'Animal', to: 'Environment', count: 1, resistance: 'Fluoroquinolone' },
  ];

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Link2 className="w-4 h-4 text-purple-500" />
        <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">One Health Signals</h3>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">3 Active</span>
      </div>

      {/* Sector Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {sectors.map((sector) => (
          <div key={sector.label} className={`${sector.bgColor} rounded-xl p-3 text-center`}>
            <sector.icon className={`w-5 h-5 ${sector.textColor} mx-auto mb-1`} />
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{sector.label}</p>
            <p className="text-lg font-bold text-slate-700 dark:text-slate-200">{sector.count}</p>
          </div>
        ))}
      </div>

      {/* Overlap Signals */}
      <div>
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Detected Overlaps</p>
        <div className="space-y-2">
          {overlaps.map((overlap, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800">
              <div className="flex items-center gap-1 text-xs">
                <span className="font-semibold text-slate-600 dark:text-slate-300">{overlap.from}</span>
                <Link2 className="w-3 h-3 text-purple-400" />
                <span className="font-semibold text-slate-600 dark:text-slate-300">{overlap.to}</span>
              </div>
              <span className="text-[10px] text-slate-500">{overlap.count} signal{overlap.count > 1 ? 's' : ''}</span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">{overlap.resistance}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
