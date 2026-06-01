import { useState } from 'react';
import { Play, ChevronRight, UserCheck, Stethoscope } from 'lucide-react';

const scenarios = [
  {
    id: 'journey1',
    title: 'Journey 1: National AMR Coordinator',
    description: 'Nairobi carbapenem-resistant K. pneumoniae outbreak detection and policy response',
    icon: UserCheck,
    steps: ['Login as National Coordinator', 'View heatmap with Nairobi hotspot', 'Investigate alert with SHAP explanation', 'Receive policy recommendations', 'Send SMS notification'],
    color: 'from-emerald-500 to-teal-600',
  },
  {
    id: 'journey2',
    title: 'Journey 2: County Veterinarian',
    description: 'Kiambu poultry fluoroquinolone resistance detection and clinical guidance',
    icon: Stethoscope,
    steps: ['Switch to County Veterinarian view', 'View Kiambu poultry resistance trend', 'Investigate fluoroquinolone alert', 'Receive vet-specific guidance', 'Access VMD SOP reference'],
    color: 'from-amber-500 to-orange-600',
  },
];

export default function DemoScenarioSelector({ onStartScenario, activeScenario }) {
  const [expanded, setExpanded] = useState(null);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Play className="w-4 h-4 text-emerald-500" />
        <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">Demo Scenarios</h3>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">July 14</span>
      </div>

      <div className="space-y-3">
        {scenarios.map((scenario) => {
          const isActive = activeScenario === scenario.id;
          const isExpanded = expanded === scenario.id;

          return (
            <div
              key={scenario.id}
              className={`rounded-xl border-2 transition-all duration-300 ${
                isActive
                  ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20'
                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
              }`}
            >
              <button
                onClick={() => {
                  setExpanded(isExpanded ? null : scenario.id);
                  onStartScenario?.(scenario.id);
                }}
                className="w-full p-4 flex items-center gap-3 text-left"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${scenario.color} flex items-center justify-center flex-shrink-0`}>
                  <scenario.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{scenario.title}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{scenario.description}</p>
                </div>
                <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </button>

              {isExpanded && (
                <div className="px-4 pb-4">
                  <div className="border-t border-slate-200 dark:border-slate-700 pt-3">
                    <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Demo Steps</p>
                    <div className="space-y-1.5">
                      {scenario.steps.map((step, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                          <span className={`w-5 h-5 rounded-full bg-gradient-to-br ${scenario.color} text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0`}>
                            {idx + 1}
                          </span>
                          {step}
                        </div>
                      ))}
                    </div>
                    {isActive && (
                      <div className="mt-3 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        Scenario Active
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
