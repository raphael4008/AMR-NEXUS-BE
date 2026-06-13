import { useForm } from 'react-hook-form';
import { CalendarIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export default function ReportFilters({ reportType, setReportType, dateRange, setDateRange, startDate, setStartDate, endDate, setEndDate, onRefresh }) {
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Report Type</label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="mdr_summary">MDR Summary</option>
            <option value="anomaly_report">Anomaly Report</option>
            <option value="sector_comparison">Sector Comparison</option>
            <option value="county_ranking">County Ranking</option>
            <option value="pathogen_wise">Pathogen‑wise Resistance</option>
            <option value="trend">MDR Trend (12 months)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500/20"
          >
            <option value="last7">Last 7 days</option>
            <option value="last30">Last 30 days</option>
            <option value="last90">Last 90 days</option>
            <option value="custom">Custom range</option>
          </select>
        </div>
        {dateRange === 'custom' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-full border border-gray-200 bg-gray-50/50 px-4 py-2 text-sm"
              />
            </div>
          </>
        )}
      </div>
      <div className="flex justify-end">
        <button
          onClick={onRefresh}
          className="px-5 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-full text-sm font-medium transition-all flex items-center gap-2"
        >
          <ChartBarIcon className="h-4 w-4" /> Refresh Report
        </button>
      </div>
    </div>
  );
}