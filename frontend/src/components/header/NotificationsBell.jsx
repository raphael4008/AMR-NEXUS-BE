import { BellIcon } from '@heroicons/react/24/outline';
import { useNotifications } from '../../hooks/useNotifications';
import { Link } from 'react-router-dom';

export default function NotificationsBell() {
  const { count, alerts } = useNotifications();

  return (
    <div className="relative group">
      <button className="relative p-2 rounded-full text-gray-500 hover:bg-white/60">
        <BellIcon className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute top-1 right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      {count > 0 && (
        <div className="hidden group-hover:block absolute top-full right-0 mt-1 w-80 bg-white rounded-xl shadow-lg border p-2 z-50">
          <p className="text-xs font-semibold text-gray-500 px-2 pt-1">Recent alerts</p>
          {alerts.map(a => (
            <Link key={a.id} to="/alerts" className="block px-2 py-1 text-sm hover:bg-gray-100 rounded">
              <span className="text-red-600">⚠️</span> {a.message}
              <span className="text-xs text-gray-400 block">{new Date(a.timestamp).toLocaleString()}</span>
            </Link>
          ))}
          <div className="border-t mt-1 pt-1 text-center">
            <Link to="/alerts" className="text-xs text-primary-600">View all →</Link>
          </div>
        </div>
      )}
    </div>
  );
}