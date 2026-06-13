import { useState } from 'react';
import HistoryActions from './HistoryActions';
import ExportSinglePDF from './ExportSinglePDF';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';

export default function HistoryTable({
  data,
  columns,
  onSelectRow,
  selectedRows,
  onDeleteSingle,
  onShare,
  onOpenDetail,
  onCompare,
}) {
  const [sortField, setSortField] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  const handleSort = (field) => {
    if (sortField === field) setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortOrder('asc'); }
  };

  const sortedData = [...data].sort((a, b) => {
    let valA = a[sortField], valB = b[sortField];
    if (sortField === 'timestamp') valA = new Date(valA), valB = new Date(valB);
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const visibleColumns = columns.filter(c => c.visible);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-3"><input type="checkbox" onChange={(e) => {
              if (e.target.checked) onSelectRow(sortedData.map(d => d.record_id));
              else onSelectRow([]);
            }} /></th>
            {visibleColumns.map(col => (
              <th key={col.id} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort(col.id)}>
                {col.label} {sortField === col.id && (sortOrder === 'asc' ? <ArrowUpIcon className="inline h-3 w-3" /> : <ArrowDownIcon className="inline h-3 w-3" />)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((record) => (
            <tr key={record.record_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => onOpenDetail(record)}>
              <td className="px-3 py-4" onClick={(e) => e.stopPropagation()}><input type="checkbox" checked={selectedRows.includes(record.record_id)} onChange={(e) => {
                if (e.target.checked) onSelectRow([...selectedRows, record.record_id]);
                else onSelectRow(selectedRows.filter(id => id !== record.record_id));
              }} /></td>
              {visibleColumns.map(col => {
                if (col.id === 'actions') return (
                  <td key={col.id} className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-2">
                      <HistoryActions recordId={record.record_id} onDelete={() => onDeleteSingle(record.record_id)} onShare={() => onShare(record.record_id)} />
                      <ExportSinglePDF record={record} />
                      <button onClick={() => onCompare(record.record_id)} className="p-1 text-gray-400 hover:text-blue-500 text-xs">Compare</button>
                    </div>
                  </td>
                );
                if (col.id === 'mdr') return <td key={col.id} className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs font-medium ${record.mdr_flag ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>{record.mdr_flag ? 'Resistant' : 'Susceptible'}</span></td>;
                if (col.id === 'anomaly') return <td key={col.id} className="px-6 py-4">{record.anomaly_detected ? <span className="text-yellow-600">⚠️ Yes</span> : 'No'}</td>;
                if (col.id === 'probability') return <td key={col.id} className="px-6 py-4">{((record.mdr_probability||0)*100).toFixed(1)}%</td>;
                if (col.id === 'date') return <td key={col.id} className="px-6 py-4">{new Date(record.timestamp).toLocaleDateString()}</td>;
                return <td key={col.id} className="px-6 py-4">{record[col.id]}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}