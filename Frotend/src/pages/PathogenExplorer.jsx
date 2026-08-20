import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Select from 'react-select';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  MapPinIcon,
  CalendarIcon,
  ArrowDownTrayIcon,
  TrophyIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import api from '../api/client';
import CountyHeatmap from '../components/analytics/CountyHeatmap';
import { saveAs } from 'file-saver';
import { counties as ALL_COUNTIES } from '../utils/constants';

export default function PathogenExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedPathogen, setSelectedPathogen] = useState(searchParams.get('pathogen') || '');
  const [selectedCounty, setSelectedCounty] = useState(searchParams.get('county') || '');
  const [startDate, setStartDate] = useState(searchParams.get('start') || '');
  const [endDate, setEndDate] = useState(searchParams.get('end') || '');

  const [pathogenOptions, setPathogenOptions] = useState([]);
  const [countyOptions, setCountyOptions] = useState([]);
  const [resistanceData, setResistanceData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Update URL when filters change
  useEffect(() => {
    const params = {};
    if (selectedPathogen) params.pathogen = selectedPathogen;
    if (selectedCounty) params.county = selectedCounty;
    if (startDate) params.start = startDate;
    if (endDate) params.end = endDate;
    setSearchParams(params, { replace: true });
  }, [selectedPathogen, selectedCounty, startDate, endDate, setSearchParams]);

  // Load options (pathogens + counties) with rates
  useEffect(() => {
    const loadOptions = async () => {
      const [pathogens, countiesData] = await Promise.all([
        api.getByPathogen(100),
        api.getTopCounties(100),
      ]);

      // Pathogens: sort by resistance (highest first)
      const sortedPathogens = pathogens
        .map(p => ({ value: p.name, label: `${p.name} (${p.resistance}%)` }))
        .sort((a, b) => {
          const aRate = parseFloat(a.label.match(/\(([\d.]+)%/)?.[1] || 0);
          const bRate = parseFloat(b.label.match(/\(([\d.]+)%/)?.[1] || 0);
          return bRate - aRate;
        });
      setPathogenOptions(sortedPathogens);

      // Counties: all from constants, merged with rates
      const allCountyOptions = ALL_COUNTIES.map(c => {
        const found = countiesData.find(d => d.county === c);
        const rate = found ? found.rate : 0;
        return { value: c, label: `${c} (${rate}%)` };
      });
      allCountyOptions.sort((a, b) => {
        const aRate = parseFloat(a.label.match(/\(([\d.]+)%/)?.[1] || 0);
        const bRate = parseFloat(b.label.match(/\(([\d.]+)%/)?.[1] || 0);
        return bRate - aRate;
      });
      setCountyOptions(allCountyOptions);
    };
    loadOptions();
  }, []);

  // Fetch data when pathogen or filters change
  useEffect(() => {
    if (!selectedPathogen) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (selectedCounty) params.append('county', selectedCounty);
        const qs = params.toString();

        const [res, trendRes] = await Promise.all([
          fetch(`http://localhost:8000/analytics/resistance_by_pathogen/${selectedPathogen}?${qs}`),
          fetch(`http://localhost:8000/analytics/pathogen_trend?pathogen_code=${selectedPathogen}&months=12&${qs}`),
        ]);

        const resistance = await res.json();
        setResistanceData(resistance);

        if (trendRes.ok) {
          const trend = await trendRes.json();
          setTrendData(trend);
        } else {
          setTrendData([]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedPathogen, selectedCounty, startDate, endDate]);

  // "Highest Resistance" button
  const selectHighestResistance = () => {
    if (pathogenOptions.length > 0) {
      const highest = pathogenOptions[0];
      setSelectedPathogen(highest.value);
    }
  };

  const exportCSV = () => {
    if (!resistanceData.length) return;
    const headers = ['Antibiotic Class', 'Resistance (%)'];
    const rows = resistanceData.map(r => [r.antibiotic_class, r.resistance]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `${selectedPathogen}_resistance_${new Date().toISOString().slice(0, 19)}.csv`);
  };

  const ActionButton = ({ onClick, icon, label, disabled, variant = 'primary' }) => {
    const base = 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2';
    const variants = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
      secondary: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-300',
      dark: 'bg-gray-800 text-white hover:bg-gray-900 focus:ring-gray-700',
    };
    return (
      <button onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]}`}>
        {icon}
        {label}
      </button>
    );
  };

  // Custom react-select styles with portal target for floating menus
  const selectStyles = {
    control: (base) => ({
      ...base,
      borderRadius: '9999px',
      borderColor: '#d1d5db',
      boxShadow: 'none',
      '&:hover': { borderColor: '#9ca3af' },
    }),
    menu: (base) => ({
      ...base,
      borderRadius: '12px',
      marginTop: '4px',
      zIndex: 9999,
    }),
    menuPortal: (base) => ({ ...base, zIndex: 9999 }),
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ChartBarIcon className="h-6 w-6 text-primary-600" />
          Pathogen Explorer
        </h1>
        <div className="flex gap-2">
          <ActionButton
            onClick={selectHighestResistance}
            icon={<TrophyIcon className="h-4 w-4" />}
            label="Highest Resistance"
            variant="dark"
            disabled={pathogenOptions.length === 0}
          />
          <ActionButton
            onClick={exportCSV}
            icon={<ArrowDownTrayIcon className="h-4 w-4" />}
            label="Export CSV"
            disabled={!resistanceData.length}
          />
        </div>
      </div>

      {/* Filters – always visible, with z-index on dropdowns */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-md border border-white/50 space-y-4 relative" style={{ overflow: 'visible' }}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {/* Pathogen */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <ChartBarIcon className="h-4 w-4 text-gray-400" />
              Pathogen
            </label>
            <Select
              options={pathogenOptions}
              value={pathogenOptions.find(o => o.value === selectedPathogen) || null}
              onChange={(option) => setSelectedPathogen(option?.value || '')}
              placeholder="Search pathogen..."
              isClearable
              styles={selectStyles}
              menuPortalTarget={document.body}
            />
          </div>

          {/* County */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <MapPinIcon className="h-4 w-4 text-gray-400" />
              County
            </label>
            <Select
              options={countyOptions}
              value={countyOptions.find(o => o.value === selectedCounty) || null}
              onChange={(option) => setSelectedCounty(option?.value || '')}
              placeholder="Search county..."
              isClearable
              styles={selectStyles}
              menuPortalTarget={document.body}
            />
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <CalendarIcon className="h-4 w-4 text-gray-400" />
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="w-full rounded-full border border-gray-300 bg-white/70 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <CalendarIcon className="h-4 w-4 text-gray-400" />
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="w-full rounded-full border border-gray-300 bg-white/70 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Clear all */}
        {(selectedPathogen || selectedCounty) && (
          <div className="flex justify-end">
            <button
              onClick={() => {
                setSelectedPathogen('');
                setSelectedCounty('');
                setStartDate('');
                setEndDate('');
              }}
              className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
            >
              <XMarkIcon className="h-4 w-4" />
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Content – shown below filters */}
      {!selectedPathogen && (
        <div className="text-center py-12 bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50">
          <ChartBarIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Select a pathogen to explore resistance patterns.</p>
        </div>
      )}

      {selectedPathogen && loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      )}

      {selectedPathogen && !loading && (
        <div className="space-y-8">
          {/* Bar chart */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-primary-600" />
              Resistance by Antibiotic Class – <span className="text-primary-600 font-bold">{selectedPathogen.toUpperCase()}</span>
            </h2>
            {resistanceData.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No resistance data available for this pathogen.</p>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={resistanceData} margin={{ top: 10, right: 30, left: 20, bottom: 70 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="antibiotic_class" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 12 }} />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Bar dataKey="resistance" fill="#8884d8" name="MDR (%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Trend */}
          {trendData.length > 0 && (
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <ArrowTrendingUpIcon className="h-5 w-5 text-primary-600" />
                MDR Trend (last 12 months) – <span className="text-primary-600 font-bold">{selectedPathogen.toUpperCase()}</span>
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={2} name="MDR Rate (%)" dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Heatmap */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <MapPinIcon className="h-5 w-5 text-primary-600" />
              Geographic Distribution – <span className="text-primary-600 font-bold">{selectedPathogen.toUpperCase()}</span>
            </h2>
            <CountyHeatmap
              startDate={startDate}
              endDate={endDate}
              pathogenCode={selectedPathogen}
              county={selectedCounty}
            />
          </div>
        </div>
      )}
    </div>
  );
}