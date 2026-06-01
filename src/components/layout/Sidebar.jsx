import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Map, TrendingUp, AlertTriangle, BookOpen,
  Activity, ChevronLeft, ChevronRight, Search, User, Settings, X
} from 'lucide-react';

const nationalLinks = [
  { to: '/national', icon: LayoutDashboard, label: 'Overview' },
  { to: '/national/map', icon: Map, label: 'Surveillance Map' },
  { to: '/national/trends', icon: TrendingUp, label: 'Trend Analysis' },
  { to: '/national/alerts', icon: AlertTriangle, label: 'Risk Alerts' },
  { to: '/national/guidance', icon: BookOpen, label: 'Guidance' },
];

const countyLinks = [
  { to: '/county', icon: LayoutDashboard, label: 'County Overview' },
  { to: '/county/alerts', icon: AlertTriangle, label: 'Local Alerts' },
  { to: '/county/guidance', icon: BookOpen, label: 'Stewardship' },
];

export default function Sidebar({ role, collapsed, onToggle, mobileOpen, onMobileClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const links = role === 'national' ? nationalLinks : countyLinks;

  const sidebarContent = (
    <aside
      className={`h-full bg-[var(--bg-secondary)]/80 backdrop-blur-2xl border border-[var(--border-primary)] rounded-[24px] flex flex-col transition-all duration-300 relative overflow-hidden ${
        collapsed ? 'w-[64px]' : 'w-[240px]'
      }`}
      style={{ boxShadow: 'var(--shadow-md)' }}
    >
      {/* Mobile close button */}
      <button
        onClick={onMobileClose}
        className="absolute top-4 right-4 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] lg:hidden z-20"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Logo */}
      <div className="px-4 pt-5 pb-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Activity className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <span className="text-[15px] font-bold text-[var(--text-primary)] tracking-tight block leading-tight">
              AMR-Nexus
            </span>
            <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-[1px]">
              One Health
            </span>
          </div>
        )}
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="px-3 mb-2">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-xs text-[var(--text-muted)]">
            <Search className="w-3.5 h-3.5" />
            <span>Quick search...</span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-2 px-2">
        {links.map((link) => {
          const isActive = location.pathname === link.to;
          return (
            <button
              key={link.to}
              onClick={() => { navigate(link.to); onMobileClose?.(); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-[13px] font-medium transition-all duration-200 rounded-xl mb-0.5 group ${
                isActive
                  ? 'text-[var(--accent-cyan)] bg-cyan-500/10'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
              }`}
              title={collapsed ? link.label : undefined}
            >
              <link.icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-[var(--accent-cyan)]' : ''}`} />
              {!collapsed && <span className="truncate">{link.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Bottom user section */}
      <div className="mt-auto border-t border-[var(--border-primary)] pt-3 pb-4 px-4">
        <button
          onClick={onToggle}
          className="hidden lg:flex items-center justify-center w-full p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors mb-3"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center">
              <User className="w-4 h-4 text-gray-200" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--text-primary)] truncate">Dr. Jane Cooper</p>
              <p className="text-[11px] text-[var(--text-muted)] truncate">
                {role === 'national' ? 'National Coordinator' : 'County Vet'}
              </p>
            </div>
            <Settings className="w-4 h-4 text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer" />
          </div>
        )}
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <div className="hidden lg:block p-3 flex-shrink-0 h-screen">
        {sidebarContent}
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onMobileClose} />
          <div className="absolute left-0 top-0 bottom-0 p-3 w-64">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}