import { Link } from 'react-router-dom';
import { ClockIcon } from '@heroicons/react/24/outline';
import { useRecentActivity } from '../../hooks/useRecentActivity';

export default function RecentActivity() {
  const { activities } = useRecentActivity();
  if (!activities.length) return null;

  return (
    <div className="relative group">
      <ClockIcon className="h-5 w-5 text-gray-500 cursor-pointer" />
      <div className="hidden group-hover:block absolute top-full right-0 mt-1 w-56 bg-white rounded-xl shadow-lg border p-2 z-50">
        <p className="text-xs font-semibold text-gray-500 px-2 pt-1">Recent pages</p>
        {activities.map(a => (
          <Link key={a.path} to={a.path} className="block px-2 py-1 text-sm hover:bg-gray-100 rounded">
            {a.title}
          </Link>
        ))}
      </div>
    </div>
  );
}