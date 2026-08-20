import { useState } from 'react';
import { AdjustmentsHorizontalIcon, XMarkIcon } from '@heroicons/react/24/outline';

const defaultColumns = [
  { id: 'pathogen', label: 'Pathogen', visible: true },
  { id: 'county', label: 'County', visible: true },
  { id: 'mdr', label: 'MDR', visible: true },
  { id: 'probability', label: 'Probability', visible: true },
  { id: 'anomaly', label: 'Anomaly', visible: true },
  { id: 'date', label: 'Date', visible: true },
  { id: 'actions', label: 'Actions', visible: true },
];

export default function HistoryColumnCustomizer({ columns, setColumns }) {
  const [open, setOpen] = useState(false);

  const toggleColumn = (id) => {
    setColumns(columns.map(c => c.id === id ? { ...c, visible: !c.visible } : c));
  };

  return (
    <>
      <button onClick={() => setOpen(true)} className="p-2 text-gray-500 hover:bg-gray-100 rounded-full">
        <AdjustmentsHorizontalIcon className="h-5 w-5" />
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-5 w-80">
            <div className="flex justify-between items-center mb-3"><h3 className="font-semibold">Show/hide columns</h3><button onClick={() => setOpen(false)}><XMarkIcon className="h-5 w-5" /></button></div>
            <div className="space-y-2">
              {columns.map(col => (
                <label key={col.id} className="flex items-center gap-2"><input type="checkbox" checked={col.visible} onChange={() => toggleColumn(col.id)} /> {col.label}</label>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}