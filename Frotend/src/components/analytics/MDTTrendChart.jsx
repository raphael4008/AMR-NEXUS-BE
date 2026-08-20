import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../api/client';

export default function MDTTrendChart({ startDate, endDate, county, onDrillDown }) {
  const [historical, setHistorical] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [showForecast, setShowForecast] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (county) params.append('county', county);
      const trend = await api.getMDRTrend(12, params.toString());
      setHistorical(trend);

      if (showForecast) {
        const forecastData = await api.getForecast(county);
        // Transform forecast to { month: 'Oct (pred)', rate: 45 } etc.
        const lastMonth = trend[trend.length-1]?.month || 'Jan';
        const forecastPoints = forecastData.map((f, i) => ({
          month: `${['Oct', 'Nov', 'Dec'][i] || 'Jan'} (pred)`,
          rate: f.predicted_mdr_rate,
          predicted: true
        }));
        setForecast(forecastPoints);
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