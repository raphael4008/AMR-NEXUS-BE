import { Bell, User, Sun, Moon, Settings, SlidersHorizontal, Menu, Search } from 'lucide-react';

export default function TopBar({ role, onToggleRole, darkMode, onToggleDark, onMenuClick }) {
  const notifications = 3;
  const isNational = role === 'national';

  return (
    <div className="px-4 lg:px-6 pt-4 pb-1">
      <header className="bg-[var(--bg-secondary)]/80 backdrop-blur-xl border border-[var(--border-primary)] rounded-2xl px-5 py-3 flex items-center justify-between gap-2">
        {/* Left section */}
        <div className="flex items-center gap-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* LIVE indicator */}
          <div className="flex items-center gap-2">
            <span className="live-pulse" />
            <span className="text-sm font-semibold text-[var(--text-primary)] tracking-wide hidden sm:inline">LIVE</span>
          </div>

          <span className="w-px h-4 bg-[var(--border-secondary)] hidden sm:block" />

          <span className="text-sm text-[var(--text-secondary)] truncate max-w-[120px] sm:max-w-none">
            {isNational ? 'National AMR Coordinator' : 'County Vet — Kiambu'}
          </span>

          {/* Search (hidden on mobile) */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-2 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-xs text-[var(--text-muted)] cursor-pointer hover:border-cyan-400/50 transition-colors">
            <Search className="w-3.5 h-3.5" />
            <span>Search pathogens, counties...</span>
            <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--bg-secondary)] border border-[var(--border-primary)] text-[var(--text-muted)]">⌘K</kbd>
          </div>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* Theme toggle */}
          <button
            onClick={onToggleDark}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <span className="w-px h-4 bg-[var(--border-secondary)] hidden sm:block" />

          {/* Role switch */}
          <button
            onClick={onToggleRole}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-[var(--accent-cyan)] hover:bg-cyan-500/10 transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{isNational ? 'County View' : 'National View'}</span>
          </button>

          <span className="w-px h-4 bg-[var(--border-secondary)] hidden sm:block" />

          {/* Notifications */}
          <button className="relative p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
            <Bell className="w-4 h-4" />
            {notifications > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center shadow-lg">
                {notifications}
              </span>
            )}
          </button>

          {/* Settings */}
          <button className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>
    </div>
  );
}