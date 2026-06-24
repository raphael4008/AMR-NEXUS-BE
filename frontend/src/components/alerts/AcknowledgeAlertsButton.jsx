import { CheckCircleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

export default function AcknowledgeAlertsButton({ alerts, onAcknowledgeAll }) {
  const unacknowledged = alerts.filter(a => !a.acknowledged);
  if (unacknowledged.length === 0) return null;

  const handleAcknowledgeAll = () => {
    if (window.confirm(`Acknowledge ${unacknowledged.length} alert(s)?`)) {
      onAcknowledgeAll(unacknowledged.map(a => a.id));
      toast.success(`${unacknowledged.length} alert(s) acknowledged`);
    }
  };

  return (
    <button
      onClick={handleAcknowledgeAll}
      className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition"
    >
      <CheckCircleIcon className="h-4 w-4" /> Acknowledge All
    </button>
  );
}