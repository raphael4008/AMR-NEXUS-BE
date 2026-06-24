import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

export default function ExportAlertsButton({ alerts }) {
  const exportCSV = () => {
    if (!alerts.length) { toast.error('No alerts to export'); return; }
    const headers = ['ID', 'Message', 'Severity', 'Type', 'Timestamp', 'Acknowledged'];
    const rows = alerts.map(a => [a.id, a.message, a.severity, a.type, a.timestamp, a.acknowledged]);
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_${new Date().toISOString().slice(0,19)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Exported');
  };

  return (
    <button onClick={exportCSV} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-full text-sm font-medium hover:bg-primary-700 transition">
      <DocumentArrowDownIcon className="h-4 w-4" /> Export CSV
    </button>
  );
}
