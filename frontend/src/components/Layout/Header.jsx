import { useRef } from 'react';
import { 
  SunIcon, 
  MoonIcon 
} from '@heroicons/react/24/outline';
import { useThemeStore } from '../../stores/themeStore';
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

  const focusSearch = () => {
    searchInputRef.current?.querySelector('input')?.focus();
  };

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
            <button onClick={toggleTheme} className="p-2 rounded-full text-gray-500 hover:bg-white/60">
              {theme === 'dark' ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
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