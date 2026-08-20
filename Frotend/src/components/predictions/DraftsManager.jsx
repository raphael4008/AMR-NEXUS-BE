import { useState } from 'react';
import { DocumentTextIcon, ChevronDownIcon, ChevronRightIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useOfflineDrafts } from '../../hooks/useOfflineDrafts';

export default function DraftsManager({ onLoadDraft, onSubmitDraft }) {
  const { drafts, removeDraft, syncDraft, clearDrafts } = useOfflineDrafts();
  const [isOpen, setIsOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);

  if (drafts.length === 0) return null;

  const handleSyncAll = async () => {
    if (syncing) return;
    setSyncing(true);
    try {
      const syncPromises = drafts.map(draft =>
        syncDraft(draft.id, onSubmitDraft)
      );
      await Promise.all(syncPromises);
      await clearDrafts();
    } catch (error) {
      console.error('Failed to sync some drafts:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5 mb-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <DocumentTextIcon className="h-5 w-5 text-primary-600" />
          <span>Offline Drafts</span>
          <span className="bg-primary-100 text-primary-800 text-xs px-2 py-0.5 rounded-full">
            {drafts.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {drafts.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleSyncAll();
              }}
              disabled={syncing}
              className="text-xs bg-primary-600 hover:bg-primary-700 text-white px-3 py-1 rounded-full flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {syncing ? (
                <ArrowPathIcon className="h-3 w-3 animate-spin" />
              ) : (
                <ArrowPathIcon className="h-3 w-3" />
              )}
              {syncing ? 'Syncing...' : 'Sync All'}
            </button>
          )}
          <span className="text-gray-500">
            {isOpen ? (
              <ChevronDownIcon className="h-5 w-5" />
            ) : (
              <ChevronRightIcon className="h-5 w-5" />
            )}
          </span>
        </div>
      </div>

      {isOpen && (
        <div className="mt-3 space-y-2">
          {drafts.map(draft => (
            <div key={draft.id} className="flex justify-between items-center text-sm bg-gray-50 p-2 rounded border border-gray-200">
              <span className="text-gray-600">
                Saved {new Date(draft.timestamp).toLocaleString()}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => onLoadDraft(draft.formData)}
                  className="text-primary-600 hover:text-primary-800 text-xs font-medium transition-colors"
                >
                  Load
                </button>
                <button
                  onClick={() => syncDraft(draft.id, onSubmitDraft)}
                  className="text-green-600 hover:text-green-800 text-xs font-medium transition-colors"
                >
                  Sync
                </button>
                <button
                  onClick={() => removeDraft(draft.id)}
                  className="text-red-600 hover:text-red-800 text-xs font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}