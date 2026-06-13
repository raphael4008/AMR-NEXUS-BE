import { useEffect, useState, useCallback, useRef } from 'react';
import { useAnalyticsFilters } from '../hooks/useAnalyticsFilters';
import api from '../api/client';
import AnalyticsFilters from '../components/analytics/AnalyticsFilters';
import AnalyticsSummaryCards from '../components/analytics/AnalyticsSummaryCards';
import MDTTrendChart from '../components/analytics/MDTTrendChart';
import AnomalyTimeline from '../components/analytics/AnomalyTimeline';
import PathogenResistanceChart from '../components/analytics/PathogenResistanceChart';
import SectorPieChart from '../components/analytics/SectorPieChart';
import CountyHeatmap from '../components/analytics/CountyHeatmap';
import PathogenAntibioticHeatmap from '../components/analytics/PathogenAntibioticHeatmap';
import ExportAnalyticsButton from '../components/analytics/ExportAnalyticsButton';
import CompareModal from '../components/analytics/CompareModal';

export default function Analytics() {
  const { filters, updateFilters } = useAnalyticsFilters();
  const [summary, setSummary] = useState({});
  const [trendData, setTrendData] = useState([]);
  const [pathogenData, setPathogenData] = useState([]);
  const [sectorData, setSectorData] = useState([]);
  const [countyList, setCountyList] = useState([]);
  const [pathogenList, setPathogenList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefreshTimer, setAutoRefreshTimer] = useState(null);
  const dashboardRef = useRef(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.county) params.append('county', filters.county);
      if (filters.pathogen) params.append('pathogen', filters.pathogen);
      const qs = params.toString();

      const [summ, trend, path, sect, counties, pathogens] = await Promise.all([
        api.getSummary(qs),
        api.getMDRTrend(12, qs),
        api.getByPathogen(20, qs),
        api.getBySector(qs),
        api.getTopCounties(20, qs),
        api.getByPathogen(100, qs),
      ]);
      setSummary(summ);
      // normaliseTrend() now returns a plain array — use directly
      setTrendData(Array.isArray(trend) ? trend : []);
      setPathogenData(path);
      setSectorData(sect);
      setCountyList(counties.map(c => c.county));
      setPathogenList(pathogens.map(p => p.name));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Auto-refresh interval
  useEffect(() => {
    if (filters.autoRefresh) {
      const timer = setInterval(fetchAll, 30000);
      setAutoRefreshTimer(timer);
      return () => clearInterval(timer);
    } else if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
      setAutoRefreshTimer(null);
    }
  }, [filters.autoRefresh, fetchAll]);

  const handleCountyClick = (county) => updateFilters({ county });
  const handlePathogenClick = (pathogen) => updateFilters({ pathogen });
  const handleRefresh = () => fetchAll();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">AMR Analytics Dashboard</h1>
        <div className="flex gap-2">
          <ExportAnalyticsButton targetId="analytics-dashboard" fileName="amr_analytics" />
          <CompareModal />
        </div>
      </div>

      <AnalyticsFilters
        startDate={filters.startDate}
        endDate={filters.endDate}
        setStartDate={(val) => updateFilters({ startDate: val })}
        setEndDate={(val) => updateFilters({ endDate: val })}
        selectedCounty={filters.county}
        setSelectedCounty={(val) => updateFilters({ county: val })}
        selectedPathogen={filters.pathogen}
        setSelectedPathogen={(val) => updateFilters({ pathogen: val })}
        autoRefresh={filters.autoRefresh}
        setAutoRefresh={(val) => updateFilters({ autoRefresh: val })}
        onRefresh={handleRefresh}
        loading={loading}
        countiesList={countyList}
        pathogensList={pathogenList}
      />

      <div id="analytics-dashboard" ref={dashboardRef} className="space-y-6">
        <AnalyticsSummaryCards summary={summary} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MDTTrendChart startDate={filters.startDate} endDate={filters.endDate} county={filters.county} onDrillDown={handleCountyClick} />
          <AnomalyTimeline startDate={filters.startDate} endDate={filters.endDate} county={filters.county} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PathogenResistanceChart data={pathogenData} onDrillDown={handlePathogenClick} />
          <SectorPieChart data={sectorData} />
        </div>

        <div className="grid grid-cols-1 gap-6">
          <CountyHeatmap startDate={filters.startDate} endDate={filters.endDate} selectedCounty={filters.county} onCountyClick={handleCountyClick} />
        </div>

        <div className="grid grid-cols-1 gap-6">
          <PathogenAntibioticHeatmap startDate={filters.startDate} endDate={filters.endDate} county={filters.county} />
        </div>
      </div>
    </div>
  );
}