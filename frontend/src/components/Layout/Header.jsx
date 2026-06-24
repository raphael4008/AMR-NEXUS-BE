import { useRef } from 'react';
import {
  SunIcon,
  MoonIcon,
  GlobeAltIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import { useThemeStore } from '../../stores/themeStore';
import { useAuth } from '../../contexts/AuthContext';
import SearchBar from '../header/SearchBar';
import NotificationsBell from '../header/NotificationsBell';
import UserMenu from '../header/UserMenu';
import Breadcrumbs from '../header/Breadcrumbs';
import OfflineIndicator from '../header/OfflineIndicator';
import KeyboardShortcuts from '../header/KeyboardShortcuts';
import RecentActivity from '../header/RecentActivity';

export default function Header({ onMenuClick }) {
  const searchInputRef = useRef(null);
  const { theme, toggleTheme } = useThemeStore();
  const { user, setRoleAndCounty } = useAuth();

  const focusSearch = () => {
    searchInputRef.current?.querySelector('input')?.focus();
  };

  const toggleRole = () => {
    console.log('🔁 Toggle role clicked. Current user:', user);
    const newRole = user?.role === 'national' ? 'county' : 'national';
    const county = newRole === 'county' ? 'Nairobi' : '';
    console.log(`Switching to ${newRole} with county: ${county}`);
    
    // Update localStorage directly as a fallback
    localStorage.setItem('role', newRole);
    localStorage.setItem('county', county);
    
    // Also update context state if available
    if (setRoleAndCounty) {
      setRoleAndCounty(newRole, county);
    } else {
      console.warn('setRoleAndCounty not available, but localStorage updated.');
    }
    
    // Force reload to pick up new role
    window.location.reload();
  };

  // Ensure user exists before rendering
  const roleLabel = user?.role === 'national' ? 'County' : 'National';
  const RoleIcon = user?.role === 'national' ? UserGroupIcon : GlobeAltIcon;

  return (
    <header className="sticky top-0 z-20 px-4 sm:px-6 pt-4">
      <div className="mx-auto bg-white/80 backdrop-blur-md rounded-2xl shadow-lg border border-white/50">
        <div className="flex items-center justify-between px-4 sm:px-5 py-2.5">
          {/* Left section */}
          <div className="flex items-center gap-3">
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 rounded-full text-gray-500 hover:bg-white/60"
              aria-label="Open sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <SearchBar ref={searchInputRef} onFocus={focusSearch} />
            <Breadcrumbs />
          </div>

          {/* Right section */}
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full text-gray-500 hover:bg-white/60"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
            </button>

            {/* Role toggle */}
            <button
              onClick={toggleRole}
              className="p-2 rounded-full text-gray-500 hover:bg-white/60 flex items-center gap-1"
              aria-label="Toggle view"
              title={`Switch to ${roleLabel} view`}
            >
              <RoleIcon className="h-5 w-5" />
              <span className="text-xs font-medium hidden sm:inline">
                {roleLabel}
              </span>
            </button>

            <OfflineIndicator />
            <RecentActivity />
            <KeyboardShortcuts onFocusSearch={focusSearch} />
            <NotificationsBell />
            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  );
}