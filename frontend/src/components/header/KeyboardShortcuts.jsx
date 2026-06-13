import { useEffect, useState } from 'react';
import { CommandLineIcon } from '@heroicons/react/24/outline';

const shortcuts = [
  { keys: ['Ctrl+K', '⌘K'], action: 'Focus search' },
  { keys: ['?'], action: 'Show shortcuts' },
  { keys: ['G', 'D'], action: 'Go to Dashboard' },
  { keys: ['G', 'P'], action: 'Go to Predict' },
  { keys: ['G', 'A'], action: 'Go to Analytics' },
];

export default function KeyboardShortcuts({ onFocusSearch }) {
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      // Cmd+K / Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onFocusSearch();
      }
      // ? key
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setShowModal(true);
      }
      // G then D, P, A (simple sequence)
      // For simplicity, we only add the modal for now
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onFocusSearch]);

  return (
    <>
      <button onClick={() => setShowModal(true)} className="p-2 text-gray-500 hover:bg-gray-100 rounded-full" title="Keyboard shortcuts (?)">
        <CommandLineIcon className="h-5 w-5" />
      </button>
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-3">Keyboard shortcuts</h3>
            <div className="space-y-2">
              {shortcuts.map(s => (
                <div key={s.keys.join('')} className="flex justify-between text-sm">
                  <span className="text-gray-500">{s.keys.join(' or ')}</span>
                  <span className="font-medium">{s.action}</span>
                </div>
              ))}
            </div>
            <button onClick={() => setShowModal(false)} className="mt-4 w-full bg-primary-600 text-white rounded-full py-2">Close</button>
          </div>
        </div>
      )}
    </>
  );
}