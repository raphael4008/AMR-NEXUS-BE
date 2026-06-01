import { useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, Clock } from 'lucide-react';

export default function MapTimeSlider({ onTimeChange }) {
  const [playing, setPlaying] = useState(false);
  const [month, setMonth] = useState(23);
  const totalMonths = 24;

  const months = [
    'Jan 2024', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    'Jan 2025', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];

  const togglePlay = () => {
    if (playing) {
      setPlaying(false);
    } else {
      setPlaying(true);
      let current = month;
      const interval = setInterval(() => {
        current++;
        if (current >= totalMonths) {
          current = 0;
          setPlaying(false);
          clearInterval(interval);
        }
        setMonth(current);
        onTimeChange?.(current);
      }, 600);
    }
  };

  return (
    <div className="card p-3 flex items-center gap-3">
      <Clock className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-500 flex-shrink-0" />
      
      <button
        onClick={() => { setMonth(0); onTimeChange?.(0); }}
        className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-400 dark:text-zinc-500 transition-colors"
      >
        <SkipBack className="w-3.5 h-3.5" />
      </button>

      <button
        onClick={togglePlay}
        className={`p-1.5 rounded-md transition-colors ${
          playing
            ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400'
            : 'hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-500 dark:text-zinc-400'
        }`}
      >
        {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
      </button>

      <button
        onClick={() => { setMonth(totalMonths - 1); onTimeChange?.(totalMonths - 1); }}
        className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-400 dark:text-zinc-500 transition-colors"
      >
        <SkipForward className="w-3.5 h-3.5" />
      </button>

      <input
        type="range"
        min={0}
        max={totalMonths - 1}
        value={month}
        onChange={(e) => {
          setMonth(parseInt(e.target.value));
          onTimeChange?.(parseInt(e.target.value));
        }}
        className="flex-1 h-1.5 rounded-full appearance-none bg-slate-200 dark:bg-zinc-700 cursor-pointer accent-teal-600"
      />

      <span className="text-[11px] font-medium text-slate-600 dark:text-zinc-400 min-w-[75px] text-right tabular-nums">
        {months[month]}
      </span>
    </div>
  );
}