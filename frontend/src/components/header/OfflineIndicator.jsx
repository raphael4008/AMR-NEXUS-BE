import { useEffect, useState } from 'react';
import { SignalIcon, CloudArrowDownIcon } from '@heroicons/react/24/outline';

export default function OfflineIndicator() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="relative group">
      <CloudArrowDownIcon className="h-5 w-5 text-gray-500" />
      <span className="absolute -top-1 -right-1 h-2 w-2 bg-yellow-500 rounded-full"></span>
      <div className="hidden group-hover:block absolute top-full right-0 mt-1 w-48 bg-gray-800 text-white text-xs rounded p-2 z-50">
        Offline – working with saved drafts. Will sync when back online.
      </div>
    </div>
  );
}