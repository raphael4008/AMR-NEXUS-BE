import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import DemoBanner from '../demo/DemoBanner';

export default function AppLayout({ role, onToggleRole, darkMode, onToggleDark }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Sidebar */}
      <Sidebar
        role={role}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden lg:pr-4 lg:py-4 lg:pl-1">
        <div className="flex-1 flex flex-col overflow-hidden lg:rounded-[20px] bg-[var(--bg-primary)] lg:border lg:border-[var(--border-primary)]">
          <DemoBanner />
          <TopBar
            role={role}
            onToggleRole={onToggleRole}
            darkMode={darkMode}
            onToggleDark={onToggleDark}
            onMenuClick={() => setMobileMenuOpen(true)}
          />
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}