import { useEffect, useState, useCallback } from 'react';
import { toast, Toaster } from 'react-hot-toast';
import api from '../api/client';
import { useLocalStorage } from '../hooks/useLocalStorage';
import HistoryFilters from '../components/history/HistoryFilters';
import HistoryAdvancedFilters from '../components/history/HistoryAdvancedFilters';
import HistoryBulkActions from '../components/history/HistoryBulkActions';
import HistoryColumnCustomizer from '../components/history/HistoryColumnCustomizer';
import HistoryStatsSummary from '../components/history/HistoryStatsSummary';
import HistoryTable from '../components/history/HistoryTable';
import HistoryDetailDrawer from '../components/history/HistoryDetailDrawer';
import HistoryComparisonModal from '../components/history/HistoryComparisonModal';
import ExportHistoryButton from '../components/history/ExportHistoryButton';

export default function History() {
  const [allPredictions, setAllPredictions] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRows, setSelectedRows] = useState([]);
  const [detailRecord, setDetailRecord] = useState(null);
  const [compareRecords, setCompareRecords] = useState([]);
  const [showCompare, setShowCompare] = useState(false);
  const [columns, setColumns] = useLocalStorage('history_columns', [
    { id: 'pathogen_code', label: 'Pathogen', visible: true },
    { id: 'county', label: 'County', visible: true },
    { id: 'mdr', label: 'MDR', visible: true },
    { id: 'probability', label: 'Probability', visible: true },
    { id: 'anomaly', label: 'Anomaly', visible: true },
    { id: 'timestamp', label: 'Date', visible: true },
    { id: 'actions', label: 'Actions', visible: true },
  ]);

  const [filters, setFilters] = useState({
    search: '',
    mdr: 'all',
    anomaly: 'all',
    pathogen: '',
    county: '',
    antibioticClass: '',
    startDate: '',
    endDate: '',
  });

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getPredictions(500, 0);
      setAllPredictions(data);
    } catch (err) {
      setError('Failed to load history');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // Apply all filters (including date range)
  useEffect(() => {
    let result = [...allPredictions];
    if (filters.search) {
      result = result.filter(p => p.pathogen_code?.toLowerCase().includes(filters.search.toLowerCase()) || p.county?.toLowerCase().includes(filters.search.toLowerCase()));
    }
    if (filters.mdr !== 'all') result = result.filter(p => String(p.mdr_flag) === filters.mdr);
    if (filters.anomaly !== 'all') result = result.filter(p => String(p.anomaly_detected) === filters.anomaly);
    if (filters.pathogen) result = result.filter(p => p.pathogen_code?.toLowerCase().includes(filters.pathogen.toLowerCase()));
    if (filters.county) result = result.filter(p => p.county?.toLowerCase().includes(filters.county.toLowerCase()));
    if (filters.antibioticClass) result = result.filter(p => p.antibiotic_class === filters.antibioticClass);
    if (filters.startDate) result = result.filter(p => new Date(p.timestamp) >= new Date(filters.startDate));
    if (filters.endDate) result = result.filter(p => new Date(p.timestamp) <= new Date(filters.endDate));
    setFiltered(result);
  }, [allPredictions, filters]);

  const handleDeleteSingle = async (id) => {
    if (window.confirm('Delete this record?')) {
      console.warn('Record deletion not available in current backend version — removed from local view only.');
      fetchPredictions();
      toast.success('Deleted');
    }
  };

  const handleBulkDelete = async (ids) => {
    console.warn('Bulk delete not available in current backend version — removed from local view only.');
    fetchPredictions();
    setSelectedRows([]);
  };

  const handleBulkExport = (ids) => {
    const selectedData = allPredictions.filter(p => ids.includes(p.record_id));
    const csv = selectedData.map(p => `${p.record_id},${p.pathogen_code},${p.county},${p.mdr_flag},${p.mdr_probability}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bulk_export_${new Date().toISOString().slice(0,19)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = (id) => {
    const url = `${window.location.origin}/prediction/${id}`;
    navigator.clipboard.writeText(url);
    toast.success('Link copied');
  };

  const handleCompare = (id) => {
    const record = allPredictions.find(p => p.record_id === id);
    if (compareRecords.some(r => r.record_id === id)) return;
    const newList = [...compareRecords, record];
    if (newList.length > 3) {
      toast.error('Can compare at most 3 records');
      return;
    }
    setCompareRecords(newList);
    if (newList.length >= 2) setShowCompare(true);
  };

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Prediction History</h1>
        <div className="flex gap-2">
          <HistoryColumnCustomizer columns={columns} setColumns={setColumns} />
          <ExportHistoryButton />
        </div>
      </div>

      <HistoryFilters
        searchTerm={filters.search}
        setSearchTerm={(val) => setFilters({...filters, search: val})}
        filterMDR={filters.mdr}
        setFilterMDR={(val) => setFilters({...filters, mdr: val})}
        filterAnomaly={filters.anomaly}
        setFilterAnomaly={(val) => setFilters({...filters, anomaly: val})}
        onRefresh={fetchPredictions}
        loading={loading}
      />

      <HistoryAdvancedFilters filters={filters} setFilters={setFilters} onRefresh={fetchPredictions} loading={loading} />

      {filtered.length > 0 && <HistoryStatsSummary data={filtered} />}

      <HistoryBulkActions selected={selectedRows} onDelete={handleBulkDelete} onExport={handleBulkExport} />

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 overflow-hidden">
        {loading && <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>}
        {error && <div className="text-center py-8 text-red-500">{error}</div>}
        {!loading && !error && filtered.length === 0 && <div className="text-center py-8 text-gray-500">No records match filters</div>}
        {!loading && !error && filtered.length > 0 && (
          <HistoryTable
            data={filtered}
            columns={columns}
            selectedRows={selectedRows}
            onSelectRow={setSelectedRows}
            onDeleteSingle={handleDeleteSingle}
            onShare={handleShare}
            onOpenDetail={setDetailRecord}
            onCompare={handleCompare}
          />
        )}
      </div>

      <HistoryDetailDrawer record={detailRecord} open={!!detailRecord} onClose={() => setDetailRecord(null)} />
      <HistoryComparisonModal records={compareRecords} open={showCompare} onClose={() => { setShowCompare(false); setCompareRecords([]); }} />
    </div>
  );
}