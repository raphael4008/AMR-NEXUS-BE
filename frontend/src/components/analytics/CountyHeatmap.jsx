import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../../api/client';

export default function CountyHeatmap({ startDate, endDate, pathogenCode = null }) {
  const [countyData, setCountyData] = useState([]);
  const [geoJson, setGeoJson] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (pathogenCode) params.append('pathogen_code', pathogenCode);
    api.getCountyMDR(params.toString()).then(setCountyData);
    fetch('/ke_counties.geojson').then(res => res.json()).then(setGeoJson);
  }, [startDate, endDate, pathogenCode]);

  const getColor = (rate) => {
    if (rate > 60) return '#b91c1c';
    if (rate > 40) return '#dc2626';
    if (rate > 20) return '#f97316';
    if (rate > 10) return '#facc15';
    return '#22c55e';
  };

  const onEachFeature = (feature, layer) => {
    const countyName = feature.properties.NAME_1;
    const data = countyData.find(d => d.county === countyName);
    const rate = data ? data.mdr_rate : 0;
    layer.bindTooltip(`${countyName}: ${rate}% MDR`);
    layer.setStyle({ fillColor: getColor(rate), fillOpacity: 0.7, weight: 1, color: 'white' });
  };

  if (!geoJson) return <div className="text-center p-4">Loading map...</div>;
  return (
    <MapContainer center={[-0.0236, 37.9062]} zoom={6} style={{ height: '400px', width: '100%' }}>
      <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
      <GeoJSON data={geoJson} onEachFeature={onEachFeature} />
    </MapContainer>
  );
}
