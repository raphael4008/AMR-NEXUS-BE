import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  useMap,
} from 'react-leaflet';
import { Loader2 } from 'lucide-react';
import { fetchChoroplethData } from '../../api/endpoints';

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 100);
    const handleResize = () => map.invalidateSize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [map]);
  return null;
}

const getColor = (level) => {
  switch (level) {
    case 'high': return '#FF5A6E';
    case 'medium': return '#F59E0B';
    case 'low': return '#00FF88';
    default: return '#94A3B8';
  }
};

const DARK_TILE = {
  url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
};
const LIGHT_TILE = {
  url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
};

export default function CountyChoroplethMap({ onCountyClick, darkMode }) {
  const containerRef = useRef(null);
  const [mapReady, setMapReady] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['choropleth'],
    queryFn: fetchChoroplethData,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          setMapReady(true);
        } else {
          setMapReady(false);
        }
      }
    });
    observer.observe(container);
    const rect = container.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) setMapReady(true);
    return () => observer.disconnect();
  }, []);

  if (isLoading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-[var(--bg-primary)]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent-cyan)]" />
      </div>
    );
  }

  const features = data?.features || [];
  const isDark = darkMode !== false;
  const currentTile = isDark ? DARK_TILE : LIGHT_TILE;
  const mapBackground = isDark ? '#0A0E17' : '#F8FAFC';

  return (
    <div
      // 🔑 Key on the outermost container forces a full remount when darkMode changes
      key={isDark ? 'dark-map' : 'light-map'}
      ref={containerRef}
      className="h-full w-full"
      style={{ minHeight: 400, background: mapBackground }}
    >
      {!mapReady && (
        <div className="h-full w-full flex items-center justify-center text-[var(--text-muted)] text-sm">
          Loading map…
        </div>
      )}
      {mapReady && (
        <MapContainer
          center={[-0.5, 37.0]}
          zoom={7}
          style={{ height: '100%', width: '100%', background: mapBackground }}
          scrollWheelZoom={false}
          zoomControl={true}
        >
          <MapResizer />
          <TileLayer
            url={currentTile.url}
            attribution={currentTile.attribution}
          />

          {features.map((feature, idx) => {
            const { county, resistanceRate, riskLevel } = feature.properties;
            const [lng, lat] = feature.geometry.coordinates;
            const radius = Math.max(16, resistanceRate * 70);
            const color = getColor(riskLevel);

            return (
              <CircleMarker
                key={idx}
                center={[lat, lng]}
                radius={radius}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.5, weight: 2 }}
                eventHandlers={{ click: () => onCountyClick?.(feature.properties) }}
              >
                <Tooltip permanent direction="top" offset={[0, -radius]}
                  className="!bg-transparent !border-0 !shadow-none !font-semibold !text-xs"
                >
                  <span style={{
                    textShadow: isDark ? '0 1px 4px black' : '0 1px 4px white',
                    color: isDark ? 'white' : '#0F172A'
                  }}>
                    {county}
                  </span>
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
}