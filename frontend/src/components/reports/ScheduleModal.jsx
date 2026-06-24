import { useState } from 'react';
import { EnvelopeIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function ScheduleModal({ isOpen, onClose, onSchedule, scheduling }) {
  const [email, setEmail] = useState('');
  const [schedule, setSchedule] = useState('weekly');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-xl">
        <div className="flex justify-between items-center p-5 border-b">
          <h3 className="text-lg font-semibold flex items-center gap-2"><EnvelopeIcon className="h-5 w-5" /> Schedule Email Report</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><XMarkIcon className="h-5 w-5" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="w-full rounded-full border border-gray-200 px-4 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
            <select value={schedule} onChange={(e) => setSchedule(e.target.value)} className="w-full rounded-full border border-gray-200 px-4 py-2">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <button onClick={onClose} className="px-4 py-2 border rounded-full text-sm">Cancel</button>
          <button onClick={() => onSchedule(email, schedule)} disabled={scheduling} className="px-4 py-2 bg-primary-600 text-white rounded-full text-sm">
            {scheduling ? 'Scheduling...' : 'Schedule'}
          </button>
        </div>
      </div>
    </div>
  );
}