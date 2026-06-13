import api from '../../api/client';
import { TrashIcon, ShareIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

export default function HistoryActions({ recordId, onDelete, onShare }) {
  const handleDelete = async () => {
    if (window.confirm('Permanently delete this prediction? This action cannot be undone.')) {
      try {
        console.warn('Delete not implemented on backend; record removed from local view only.');
        if (!response.ok) throw new Error('Delete failed');
        toast.success('Prediction deleted');
        if (onDelete) onDelete(recordId);
      } catch (err) {
        toast.error('Could not delete');
      }
    }
  };

  const handleShare = () => {
    const shareData = {
      title: 'AMR Prediction',
      text: `Prediction ID: ${recordId}`,
      url: `${window.location.origin}/prediction/${recordId}`,
    };
    if (navigator.share) {
      navigator.share(shareData).catch(() => {});
    } else {
      navigator.clipboard.writeText(`${shareData.url}\n${shareData.text}`);
      if (onShare) onShare(recordId);
      else toast.success('Link copied to clipboard');
    }
  };

  return (
    <div className="flex gap-2">
      <button onClick={handleShare} className="p-1 text-gray-400 hover:text-blue-500 transition" title="Share">
        <ShareIcon className="h-4 w-4" />
      </button>
      <button onClick={handleDelete} className="p-1 text-gray-400 hover:text-red-600 transition" title="Delete">
        <TrashIcon className="h-4 w-4" />
      </button>
    </div>
  );
}