import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function HistoryDetailDrawer({ record, open, onClose }) {
  if (!record) return null;

  const [note, setNote] = useState(record.user_note || '');

  const saveNote = () => {
    // In real app, call API to save note
    console.log('Save note', note);
    alert('Note saved (mock)');
  };

  return (
    <Transition show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <div className="fixed inset-0 bg-black/30" />
        <div className="fixed inset-y-0 right-0 flex max-w-full">
          <Dialog.Panel className="w-screen max-w-md bg-white shadow-xl">
            <div className="flex justify-between items-center p-4 border-b">
              <Dialog.Title className="text-lg font-semibold">Prediction Details</Dialog.Title>
              <button onClick={onClose}><XMarkIcon className="h-5 w-5" /></button>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto h-[calc(100vh-80px)]">
              <div><span className="text-xs text-gray-500">Record ID</span><p className="text-sm font-mono">{record.record_id}</p></div>
              <div><span className="text-xs text-gray-500">Pathogen</span><p className="font-medium">{record.pathogen_code?.toUpperCase()}</p></div>
              <div><span className="text-xs text-gray-500">County</span><p>{record.county}</p></div>
              <div><span className="text-xs text-gray-500">MDR</span><p className={record.mdr_flag ? 'text-red-600 font-bold' : 'text-green-600'}>{record.mdr_flag ? 'Resistant' : 'Susceptible'}</p></div>
              <div><span className="text-xs text-gray-500">Probability</span><p>{((record.mdr_probability || 0)*100).toFixed(1)}%</p></div>
              <div><span className="text-xs text-gray-500">Anomaly</span><p>{record.anomaly_detected ? 'Yes' : 'No'}</p></div>
              <div><span className="text-xs text-gray-500">Timestamp</span><p>{new Date(record.timestamp).toLocaleString()}</p></div>
              <div><span className="text-xs text-gray-500">SHAP top feature</span><p className="text-sm">{record.shap_top_feature?.replace(/_/g, ' ') || 'N/A'}</p></div>
              <div><span className="text-xs text-gray-500">SHAP value</span><p>{record.shap_value?.toFixed(4)}</p></div>
              <div className="border-t pt-2">
                <label className="text-xs text-gray-500 block mb-1">Private note</label>
                <textarea rows="3" value={note} onChange={e => setNote(e.target.value)} className="w-full border rounded p-2 text-sm" />
                <button onClick={saveNote} className="mt-2 text-xs bg-primary-600 text-white px-3 py-1 rounded-full">Save note</button>
              </div>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </Transition>
  );
}