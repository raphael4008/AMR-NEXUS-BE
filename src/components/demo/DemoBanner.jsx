import { FlaskConical } from 'lucide-react';

export default function DemoBanner() {
  return (
    <div className="bg-amber-50/80 dark:bg-amber-950/30 border-b border-amber-200/50 dark:border-amber-800/30 px-6 py-2">
      <div className="flex items-center gap-2.5 text-[11px]">
        <FlaskConical className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
        <span className="font-semibold text-amber-700 dark:text-amber-400">Functional Proof-of-Concept</span>
        <span className="text-amber-400 dark:text-amber-600">·</span>
        <span className="text-amber-600/70 dark:text-amber-400/70">High-fidelity synthetic data. Not a live operational surveillance system.</span>
      </div>
    </div>
  );
}
