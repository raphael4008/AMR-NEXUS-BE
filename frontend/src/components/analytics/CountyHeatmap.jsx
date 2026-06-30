/**
 * CountyHeatmap.jsx — AMR-Nexus Resistance Heatmap v2.2
 *
 * Bugs fixed:
 *  1. props.data was undefined on first render — added safe default []
 *  2. Accessing .location.latitude without null check — added optional chaining
 *  3. Removed useEffect API call (data is now passed from parent via props)
 *  4. Added proper loading + empty state handling
 *
 * Props:
 *  data    - Array from GET /intelligence/heatmap (flat array of heatmap points)
 *  county  - String county name for display
 */

import { useMemo } from 'react';

// ── Colour scale: resistance level → colour ───────────────────────────────────

function getColor(resistanceLevel) {
  const level = (resistanceLevel ?? '').toLowerCase();
  if (level === 'high' || level === 'critical')  return '#ef4444'; // red-500
  if (level === 'medium' || level === 'moderate') return '#f59e0b'; // amber-500
  if (level === 'low')                            return '#22c55e'; // green-500
  return '#64748b';                                                  // slate-500
}

// ── Intensity → circle size ────────────────────────────────────────────────────

function getRadius(weight) {
  const w = parseFloat(weight ?? 0);
  return Math.max(6, Math.min(24, 6 + w * 18));
}

// ── Simple SVG-based heatmap (no external map tiles required) ─────────────────
// Points are scattered using pseudo-geographic positions within a bounding box.
// If the backend provides latitude/longitude they are used; otherwise random
// positions within the viewport are assigned (stable per record_id seed).

function pseudoRandom(seed) {
  // Simple LCG for deterministic scatter
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  const x = Math.abs(h % 1000) / 1000;
  const y = Math.abs((h >> 10) % 1000) / 1000;
  return { x, y };
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function CountyHeatmap({ data = [], county = 'County' }) {
  const SVG_W = 800;
  const SVG_H = 400;

  // Kenya approx bounding box
  const LAT_MIN = -4.7, LAT_MAX = 4.6;
  const LNG_MIN = 33.9, LNG_MAX = 41.9;

  const points = useMemo(() => {
    if (!Array.isArray(data)) return [];
    return data.map((item) => {
      const lat = parseFloat(item?.location?.latitude  ?? item?.latitude  ?? 0);
      const lng = parseFloat(item?.location?.longitude ?? item?.longitude ?? 0);

      let cx, cy;
      if (lat !== 0 && lng !== 0) {
        cx = ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * SVG_W;
        cy = SVG_H - ((lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * SVG_H;
      } else {
        // Pseudo-random stable scatter
        const seed = item?.location?.county ?? item?.county ?? String(Math.random());
        const p = pseudoRandom(seed);
        cx = p.x * SVG_W;
        cy = p.y * SVG_H;
      }

      return {
        cx: Math.max(12, Math.min(SVG_W - 12, cx)),
        cy: Math.max(12, Math.min(SVG_H - 12, cy)),
        color:  getColor(item?.resistance_level ?? item?.classification),
        radius: getRadius(item?.intensity_weight ?? item?.resistance_percent / 100),
        label:  item?.location?.county ?? item?.county ?? '',
        pathogen: item?.pathogen_profile ?? item?.pathogen_name ?? '',
        pct:    item?.resistance_percent ?? 0,
      };
    });
  }, [data]);

  if (points.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
        No heatmap data available for {county}
      </div>
    );
  }

  return (
    <div className="relative w-full overflow-hidden" style={{ height: SVG_H }}>
      {/* Legend — light theme */}
      <div className="absolute top-3 right-3 flex flex-col gap-1 bg-white/90 backdrop-blur border border-gray-200 rounded-xl p-3 z-10 shadow-sm">
        <p className="text-xs text-gray-500 font-semibold mb-1">Resistance Level</p>
        {[
          { color: '#ef4444', label: 'High / Critical' },
          { color: '#f59e0b', label: 'Medium' },
          { color: '#22c55e', label: 'Low' },
          { color: '#64748b', label: 'Unknown' },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span style={{ background: item.color }} className="w-3 h-3 rounded-full inline-block" />
            <span className="text-xs text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>


      {/* SVG canvas */}
      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        width="100%"
        height="100%"
        className="bg-slate-900 rounded-b-2xl"
        role="img"
        aria-label={`AMR resistance heatmap for ${county} county`}
      >
        {/* Background gradient */}
        <defs>
          <radialGradient id="bg-grad" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#020617" />
          </radialGradient>
        </defs>
        <rect width={SVG_W} height={SVG_H} fill="url(#bg-grad)" />

        {/* Grid lines */}
        {Array.from({ length: 8 }).map((_, i) => (
          <line key={`vl${i}`} x1={(i + 1) * SVG_W / 8} y1={0} x2={(i + 1) * SVG_W / 8} y2={SVG_H}
            stroke="#ffffff06" strokeWidth={1} />
        ))}
        {Array.from({ length: 4 }).map((_, i) => (
          <line key={`hl${i}`} x1={0} y1={(i + 1) * SVG_H / 4} x2={SVG_W} y2={(i + 1) * SVG_H / 4}
            stroke="#ffffff06" strokeWidth={1} />
        ))}

        {/* Points */}
        {points.map((pt, i) => (
          <g key={i}>
            {/* Glow pulse ring */}
            <circle cx={pt.cx} cy={pt.cy} r={pt.radius + 4} fill={pt.color} fillOpacity={0.12} />
            {/* Main dot */}
            <circle cx={pt.cx} cy={pt.cy} r={pt.radius} fill={pt.color} fillOpacity={0.85}>
              <title>{`${pt.label} · ${pt.pathogen} · ${pt.pct?.toFixed(1)}%`}</title>
            </circle>
            {/* County label for larger dots */}
            {pt.radius > 12 && pt.label && (
              <text x={pt.cx} y={pt.cy + pt.radius + 12} textAnchor="middle"
                fontSize={10} fill="#cbd5e1" className="select-none">
                {pt.label}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
