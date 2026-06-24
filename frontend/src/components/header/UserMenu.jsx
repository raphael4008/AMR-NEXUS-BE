import { useState } from 'react';
import { Link } from 'react-router-dom';
import { UserCircleIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../hooks/useAuth';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 p-1 rounded-full hover:bg-white/60"
      >
        <UserCircleIcon className="h-8 w-8 text-gray-400" />
        <span className="hidden md:inline text-sm font-medium text-gray-700">{user.name}</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)}></div>
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border py-1 z-20">
            <div className="px-4 py-3 border-b">
              <p className="text-sm font-semibold">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
              <p className="text-xs text-primary-600 mt-1 capitalize">Role: {user.role}</p>
            </div>
            <Link to="/profile" className="flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-50" onClick={() => setOpen(false)}>
              <UserCircleIcon className="h-4 w-4 text-gray-400" /> Profile
            </Link>
            <Link to="/settings" className="flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-50" onClick={() => setOpen(false)}>
              <Cog6ToothIcon className="h-4 w-4 text-gray-400" /> Settings
            </Link>
            <hr className="my-1" />
            <button className="flex items-center gap-3 w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50" onClick={logout}>
              <ArrowRightOnRectangleIcon className="h-4 w-4" /> Logout
            </button>
          </div>
        </>
      )}
    </div>
  );
}