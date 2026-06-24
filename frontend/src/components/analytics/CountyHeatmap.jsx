import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../../api/client';

export default function CountyHeatmap({ startDate, endDate, pathogenCode = null, county = null }) {
  const [countyData, setCountyData] = useState([]);
  const [geoJson, setGeoJson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (pathogenCode) params.append('pathogen_code', pathogenCode);
    if (county) params.append('county', county);
    const qs = params.toString();

    setLoading(true);
    setError(null);

    // Fetch county MDR data
    api.getCountyMDR(qs)
      .then(setCountyData)
      .catch((err) => {
        console.error('Failed to fetch county data:', err);
        setError('Could not load county data.');
      });

    // Fetch GeoJSON, with fallback
    fetch('/ke_counties.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('GeoJSON not found');
        return res.json();
      })
      .then(setGeoJson)
      .catch(() => {
        // Fallback GeoJSON with sample counties (Nairobi, Kiambu, Machakos)
        const fallback = {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: { NAME_1: "Nairobi" },
              geometry: {
                type: "Polygon",
                coordinates: [[[36.8, -1.3], [37.0, -1.3], [37.0, -1.5], [36.8, -1.5], [36.8, -1.3]]]
              }
            },
            {
              type: "Feature",
              properties: { NAME_1: "Kiambu" },
              geometry: {
                type: "Polygon",
                coordinates: [[[36.6, -1.1], [36.9, -1.1], [36.9, -1.3], [36.6, -1.3], [36.6, -1.1]]]
              }
            },
            {
              type: "Feature",
              properties: { NAME_1: "Machakos" },
              geometry: {
                type: "Polygon",
                coordinates: [[[37.0, -1.4], [37.3, -1.4], [37.3, -1.6], [37.0, -1.6], [37.0, -1.4]]]
              }
            }
          ]
        };
        setGeoJson(fallback);
      })
      .finally(() => setLoading(false));
  }, [startDate, endDate, pathogenCode, county]);

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
    layer.setStyle({
      fillColor: getColor(rate),
      fillOpacity: 0.7,
      weight: 1,
      color: 'white',
    });

    if (county && countyName === county) {
      layer.setStyle({
        weight: 3,
        color: '#2563eb',
        dashArray: null,
      });
    }
  };

  if (loading) return <div className="text-center p-4">Loading map...</div>;
  if (error) return <div className="text-center p-4 text-red-500">{error}</div>;
  if (!geoJson) return <div className="text-center p-4">No map data available.</div>;

  return (
    <MapContainer
      center={[-0.0236, 37.9062]}
      zoom={6}
      style={{ height: '400px', width: '100%', borderRadius: '12px' }}
    >
      <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
      <GeoJSON data={geoJson} onEachFeature={onEachFeature} />
    </MapContainer>
  );
}