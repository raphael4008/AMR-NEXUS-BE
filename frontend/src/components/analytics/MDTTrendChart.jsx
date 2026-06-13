import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../api/client';

export default function MDTTrendChart({ startDate, endDate, county, onDrillDown }) {
  const [historical, setHistorical] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [showForecast, setShowForecast] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate)   params.append('end_date',   endDate);
        if (county)    params.append('county',      county);

        // normaliseTrend() returns a plain [{month, rate, ...}] array
        const series = await api.getMDRTrend(12, params.toString());
        setHistorical(Array.isArray(series) ? series : []);

        if (showForecast) {
          const forecastSeries = await api.getForecast(params.toString());
          const safe = Array.isArray(forecastSeries) ? forecastSeries : [];
          // Mark forecast points so the chart can style them differently
          setForecast(safe.map((f, i) => ({
            ...f,
            month: `${f.month ?? ['Oct','Nov','Dec'][i] ?? 'Fut'} (pred)`,
            predicted: true,
          })));
        }
      } catch (err) {
        console.error('MDTTrendChart fetch error:', err);
      }
    };
    fetchData();
  }, [startDate, endDate, county, showForecast]);

  const combinedData = [...historical, ...(showForecast ? forecast : [])];

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-md font-semibold text-gray-800">MDR Trend (with forecast)</h3>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showForecast} onChange={e => setShowForecast(e.target.checked)} /> Show forecast</label>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={combinedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis domain={[0, 100]} unit="%" />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} name="MDR Rate (%)" />
          {showForecast && <Line type="monotone" dataKey="rate" stroke="#f97316" strokeDasharray="5 5" name="Forecast" />}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}