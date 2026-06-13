import api from '../../api/client';
// src/components/dashboard/QuickActions.jsx
import { Link } from 'react-router-dom';
import { ChartBarIcon, DocumentArrowDownIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

export default function QuickActions() {
  const handleExportCSV = async () => {
    try {
      await api.exportRecordsCSV();
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `amr_export_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
      a.remove();
    } catch (err) {
      alert('Export failed');
    }
  };

  return (
    <div className="flex gap-3">
      <Link to="/predict" className="px-4 py-2 bg-primary-600 text-white rounded-full text-sm font-medium flex items-center gap-2 hover:bg-primary-700 transition">
        <ChartBarIcon className="h-4 w-4" /> New Prediction
      </Link>
      <button onClick={handleExportCSV} className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition">
        <DocumentArrowDownIcon className="h-4 w-4" /> Export CSV
      </button>
      <Link to="/reports" className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition">
        <DocumentTextIcon className="h-4 w-4" /> Full Reports
      </Link>
    </div>
  );
}