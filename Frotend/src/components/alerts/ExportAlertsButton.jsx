import { useState } from 'react';
import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../../api/client';

export default function ExportAlertsButton({
  alerts: propAlerts = null,
  county = '',
  startDate = '',
  endDate = '',
  severity = 'all',
  type = 'all',
  showAcknowledged = true,
  limit = 10000,
}) {
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    try {
      setLoading(true);

      let alertsData = propAlerts;

      if (!alertsData) {
        const params = new URLSearchParams();
        if (county) params.append('county', county);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (severity !== 'all') params.append('severity', severity);
        if (type !== 'all') params.append('type', type);
        if (showAcknowledged) params.append('include_acknowledged', 'true');
        params.append('limit', limit);
        alertsData = await api.getAlerts(params.toString());
      }

      if (!alertsData || alertsData.length === 0) {
        toast.error('No alerts to export');
        return;
      }

      const headers = [
        'ID',
        'County',
        'Message',
        'Severity',
        'Type',
        'Timestamp',
        'Acknowledged',
        'Pathogen',
        'Record ID',
        'Details',
      ];

      const rows = alertsData.map((a) => [
        a.id || a.alert_id || '',
        a.county || '',
        `"${(a.message || '').replace(/"/g, '""')}"`,
        a.severity || inferSeverity(a.message),
        a.type || a.alert_type || 'anomaly',
        a.created_at || a.timestamp || '',
        a.is_read || a.acknowledged ? 'Yes' : 'No',
        a.pathogen_code || '',
        a.record_id || '',
        `"${(a.details || '').replace(/"/g, '""')}"`,
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const dateStr = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      link.download = `alerts_${dateStr}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success(`Exported ${alertsData.length} alerts`);
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export alerts');
    } finally {
      setLoading(false);
    }
  };

  function inferSeverity(message) {
    const msg = (message || '').toLowerCase();
    if (msg.includes('critical') || msg.includes('high') || msg.includes('spike')) return 'high';
    if (msg.includes('warning') || msg.includes('medium')) return 'medium';
    return 'low';
  }

  return (
    <button
      onClick={handleExport}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-full text-sm font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500"
    >
      {loading ? (
        <>
          <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          Exporting...
        </>
      ) : (
        <>
          <DocumentArrowDownIcon className="h-4 w-4" />
          Export CSV
        </>
      )}
    </button>
  );
}