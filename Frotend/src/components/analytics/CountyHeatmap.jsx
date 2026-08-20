import { useEffect, useState, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import api from '../../api/client';

function Legend({ metric, maxValue, colorScale }) {
  const steps = 5;
  const labels = [];
  for (let i = 0; i <= steps; i++) {
    const val = (maxValue / steps) * i;
    labels.push(val.toFixed(1));
  }
  return (
    <div className="absolute bottom-6 left-6 z-[1000] bg-white/90 backdrop-blur-sm p-3 rounded-xl shadow-md text-sm border border-white/50">
      <p className="font-semibold text-gray-700 mb-1">
        {metric === 'mdr_rate' ? 'MDR Rate (%)' :
         metric === 'total_isolates' ? 'Isolates' :
         'Anomalies'}
      </p>
      {labels.map((label, i) => {
        const color = colorScale((maxValue / steps) * i);
        return (
          <div key={i} className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 rounded" style={{ backgroundColor: color }}></span>
            <span className="text-xs text-gray-600">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

function FitBounds({ geoJson }) {
  const map = useMap();
  useEffect(() => {
    if (geoJson) {
      const layer = new L.GeoJSON(geoJson);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [geoJson, map]);
  return null;
}

function ZoomToCounty({ geoJson, selectedCounty }) {
  const map = useMap();
  useEffect(() => {
    if (!geoJson || !selectedCounty) return;
    const feature = geoJson.features.find(f => {
      const name = f.properties.county || f.properties.NAME_1 || f.properties.ADM1_EN;
      return name && name.toLowerCase() === selectedCounty.toLowerCase();
    });
    if (feature) {
      const layer = new L.GeoJSON(feature);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [geoJson, selectedCounty, map]);
  return null;
}

export default function CountyHeatmap({
  startDate,
  endDate,
  pathogenCode = null,
  selectedCounty = null,
  onCountySelect = () => {},
  onMetricChange = () => {},
  onDateRangeChange = () => {},
}) {
  const [countyData, setCountyData] = useState([]);
  const [anomalyData, setAnomalyData] = useState({});
  const [geoJson, setGeoJson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('mdr_rate');
  const [timeRange, setTimeRange] = useState(6);

  const countyCentroids = useMemo(() => {
    if (!geoJson) return {};
    const centroids = {};
    geoJson.features.forEach(feature => {
      const name = feature.properties.county || feature.properties.NAME_1;
      if (!name) return;
      const coords = feature.geometry.coordinates[0];
      let lat = 0, lng = 0, count = 0;
      coords.forEach(coord => {
        lng += coord[0];
        lat += coord[1];
        count++;
      });
      centroids[name] = [lat / count, lng / count];
    });
    return centroids;
  }, [geoJson]);

  const buildParams = useCallback(() => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (pathogenCode) params.append('pathogen_code', pathogenCode);
    if (selectedCounty) params.append('county', selectedCounty);
    if (timeRange) params.append('months', timeRange);
    return params.toString();
  }, [startDate, endDate, pathogenCode, selectedCounty, timeRange]);

  useEffect(() => {
    const qs = buildParams();
    setLoading(true);
    setError(null);

    const geojsonSources = [
      'https://raw.githubusercontent.com/CodeForAfrica/Kenya-GeoJSON/master/counties.geojson',
      '/ke_counties.geojson'
    ];

    const fetchGeoJson = async () => {
      for (const url of geojsonSources) {
        try {
          const res = await fetch(url);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          if (data.features && data.features.length > 0) {
            return data;
          }
        } catch (e) {
          console.warn(`Failed to fetch GeoJSON from ${url}`, e);
        }
      }
      throw new Error('Could not load county boundaries. Please check your internet connection or ensure ke_counties.geojson is placed in the public folder.');
    };

    Promise.all([
      api.getCountyMDR(qs),
      api.getAlerts(qs),
      fetchGeoJson()
    ])
    .then(([countyData, alerts, geojson]) => {
      setCountyData(countyData || []);
      const anomalyMap = {};
      (alerts || []).forEach(alert => {
        anomalyMap[alert.county] = (anomalyMap[alert.county] || 0) + 1;
      });
      setAnomalyData(anomalyMap);
      setGeoJson(geojson);
    })
    .catch(err => {
      console.error('Failed to load map data:', err);
      setError(err.message || 'Could not load map data.');
    })
    .finally(() => setLoading(false));
  }, [buildParams]);

  const colorScale = useCallback((value) => {
    const max = selectedMetric === 'mdr_rate' ? 100 :
                selectedMetric === 'total_isolates' ? Math.max(...countyData.map(d => d.total || 0), 10) :
                Math.max(...Object.values(anomalyData), 1);
    const normalized = Math.min(value / max, 1);
    const r = Math.round(255 * (1 - normalized));
    const g = Math.round(255 * normalized);
    return `rgb(${r}, ${g}, 0)`;
  }, [selectedMetric, countyData, anomalyData]);

  const onEachFeature = useCallback((feature, layer) => {
    const countyName = feature.properties.county || feature.properties.NAME_1 || feature.properties.ADM1_EN;
    if (!countyName) return;

    const data = countyData.find(d => d.county?.toLowerCase() === countyName.toLowerCase());
    const value = data ?
      (selectedMetric === 'mdr_rate' ? data.mdr_rate :
       selectedMetric === 'total_isolates' ? data.total :
       (anomalyData[countyName] || 0)) : 0;

    const tooltipContent = `
      <div style="font-size:14px;">
        <strong>${countyName}</strong><br/>
        MDR Rate: ${data?.mdr_rate || 0}%<br/>
        Isolates: ${data?.total || 0}<br/>
        Anomalies: ${anomalyData[countyName] || 0}
      </div>
    `;
    layer.bindTooltip(tooltipContent, { className: 'custom-tooltip' });

    const isSelected = selectedCounty && countyName.toLowerCase() === selectedCounty.toLowerCase();

    layer.setStyle({
      fillColor: colorScale(value),
      fillOpacity: 0.8,
      weight: isSelected ? 4 : 1,
      color: isSelected ? '#2563eb' : '#ffffff',
      dashArray: isSelected ? null : null,
    });

    layer.on('click', () => {
      onCountySelect(countyName);
    });
  }, [countyData, anomalyData, selectedMetric, colorScale, selectedCounty, onCountySelect]);

  const maxValue = useMemo(() => {
    if (selectedMetric === 'mdr_rate') return 100;
    if (selectedMetric === 'total_isolates') {
      const maxTotal = Math.max(...countyData.map(d => d.total || 0), 10);
      return maxTotal;
    }
    const maxAnomaly = Math.max(...Object.values(anomalyData), 1);
    return maxAnomaly;
  }, [selectedMetric, countyData, anomalyData]);

  const handleMetricChange = (e) => {
    const metric = e.target.value;
    setSelectedMetric(metric);
    onMetricChange(metric);
  };

  const handleTimeChange = (e) => {
    const months = parseInt(e.target.value);
    setTimeRange(months);
    onDateRangeChange(months);
  };

  if (loading) return <div className="text-center p-4">Loading map...</div>;
  if (error) return <div className="text-center p-4 text-red-500">{error}</div>;
  if (!geoJson) return <div className="text-center p-4">No map data available.</div>;

  return (
    <div className="relative">
      <div className="absolute top-4 left-4 z-[1000] flex gap-3 bg-white/90 p-2 rounded-xl shadow-md">
        <select
          value={selectedMetric}
          onChange={handleMetricChange}
          className="border border-gray-300 rounded-lg px-3 py-1 text-sm focus:ring-2 focus:ring-primary-500"
        >
          <option value="mdr_rate">MDR Rate (%)</option>
          <option value="total_isolates">Isolates Count</option>
          <option value="anomaly_count">Anomalies</option>
        </select>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">Months:</span>
          <input
            type="range"
            min="1"
            max="12"
            value={timeRange}
            onChange={handleTimeChange}
            className="w-24"
          />
          <span className="text-xs text-gray-600">{timeRange}</span>
        </div>
      </div>

      <MapContainer
        center={[-0.0236, 37.9062]}
        zoom={6}
        style={{ height: '500px', width: '100%', borderRadius: '12px' }}
        className="z-0"
      >
        <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
        <GeoJSON
          key={selectedCounty || 'all'}
          data={geoJson}
          onEachFeature={onEachFeature}
        />

        {Object.entries(anomalyData).map(([county, count]) => {
          const centroid = countyCentroids[county];
          if (!centroid || count === 0) return null;
          return (
            <CircleMarker
              key={county}
              center={centroid}
              radius={Math.min(10 + count * 2, 20)}
              color="red"
              fillColor="red"
              fillOpacity={0.6}
              weight={2}
              eventHandlers={{
                click: () => onCountySelect(county),
              }}
            >
              <Popup>
                <strong>{county}</strong><br/>
                Anomalies: {count}
              </Popup>
            </CircleMarker>
          );
        })}

        <ZoomToCounty geoJson={geoJson} selectedCounty={selectedCounty} />
        <FitBounds geoJson={geoJson} />
      </MapContainer>

      <Legend metric={selectedMetric} maxValue={maxValue} colorScale={colorScale} />
    </div>
  );
}