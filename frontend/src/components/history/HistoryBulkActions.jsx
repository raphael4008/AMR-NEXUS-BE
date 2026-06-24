import { TrashIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

export default function HistoryBulkActions({ selected, onDelete, onExport }) {
  const handleBulkDelete = async () => {
    if (selected.length === 0) return;
    if (window.confirm(`Delete ${selected.length} record(s) permanently?`)) {
      await onDelete(selected);
      toast.success(`${selected.length} record(s) deleted`);
    }
  };

  const handleBulkExport = () => {
    if (selected.length === 0) return;
    onExport(selected);
  };

  if (selected.length === 0) return null;

  return (
    <div className="bg-primary-50 rounded-xl p-3 flex items-center justify-between">
      <span className="text-sm font-medium text-primary-800">{selected.length} selected</span>
      <div className="flex gap-2">
        <button onClick={handleBulkExport} className="flex items-center gap-1 px-3 py-1 bg-white rounded-full text-xs shadow"><DocumentArrowDownIcon className="h-3 w-3" /> Export</button>
        <button onClick={handleBulkDelete} className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs"><TrashIcon className="h-3 w-3" /> Delete</button>
      </div>
    </div>
  );
}