import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function HistoryComparisonModal({ records, open, onClose }) {
  if (!records.length) return null;

  return (
    <Transition show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <div className="fixed inset-0 bg-black/30" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="w-full max-w-4xl bg-white rounded-2xl shadow-xl">
            <div className="flex justify-between items-center p-4 border-b">
              <Dialog.Title className="text-lg font-semibold">Compare Predictions</Dialog.Title>
              <button onClick={onClose}><XMarkIcon className="h-5 w-5" /></button>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead><tr><th className="border p-2 bg-gray-50">Field</th>{records.map(r => <th key={r.record_id} className="border p-2">{r.pathogen_code?.toUpperCase()}<br/><span className="text-xs font-normal">{new Date(r.timestamp).toLocaleDateString()}</span></th>)}</tr></thead>
                <tbody>
                  <tr><td className="border p-2 font-medium">County</td>{records.map(r => <td key={r.record_id} className="border p-2">{r.county}</td>)}</tr>
                  <tr><td className="border p-2 font-medium">MDR</td>{records.map(r => <td key={r.record_id} className="border p-2">{r.mdr_flag ? 'Resistant' : 'Susceptible'}</td>)}</tr>
                  <tr><td className="border p-2 font-medium">Probability</td>{records.map(r => <td key={r.record_id} className="border p-2">{((r.mdr_probability||0)*100).toFixed(1)}%</td>)}</tr>
                  <tr><td className="border p-2 font-medium">Anomaly</td>{records.map(r => <td key={r.record_id} className="border p-2">{r.anomaly_detected ? 'Yes' : 'No'}</td>)}</tr>
                </tbody>
              </table>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </Transition>
  );
}