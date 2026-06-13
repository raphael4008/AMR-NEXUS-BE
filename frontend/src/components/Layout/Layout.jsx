import { useState, useEffect, useRef, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarRef = useRef(null);

  // Close sidebar when Escape key is pressed
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && sidebarOpen) setSidebarOpen(false);
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [sidebarOpen]);

  const handleOverlayClick = useCallback((e) => {
    if (sidebarRef.current && !sidebarRef.current.contains(e.target)) {
      setSidebarOpen(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Mobile sidebar overlay (unchanged) */}
      <div
        className={`fixed inset-0 z-40 lg:hidden transition-opacity duration-300 ${
          sidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleOverlayClick}
      >
        <div className="absolute inset-0 bg-gray-600 bg-opacity-75" />
        <div
          ref={sidebarRef}
          className={`relative flex flex-col w-64 bg-white h-full shadow-xl transform transition-transform duration-300 ease-in-out ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation menu"
        >
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-lg font-semibold text-gray-900">AMR‑Nexus</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
              aria-label="Close menu"
            >
              ✕
            </button>
          </div>
          <Sidebar mobile onNavigate={() => setSidebarOpen(false)} />
        </div>
      </div>

      {/* ✅ Desktop sidebar – FLOATING, OVAL PILLS, NO TOUCH TO HEADER/FOOTER */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:items-center lg:justify-center lg:pointer-events-none">
        <div className="lg:relative lg:w-64 lg:mx-6 lg:my-8 lg:pointer-events-auto">
          <div className="flex flex-col bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-100/50 overflow-hidden">
            <div className="pt-6 pb-2 px-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 bg-primary-600 rounded-xl flex items-center justify-center shadow-sm">
                  <span className="text-white font-bold text-lg">A</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">AMR‑Nexus</span>
              </div>
            </div>
            <Sidebar />
            <div className="p-4 text-xs text-center text-gray-400 border-t border-gray-100">
              v1.0 • Secure
            </div>
          </div>
        </div>
      </div>

      {/* Main content – shifted right to accommodate floating sidebar */}
      <div className="lg:pl-72 flex flex-col flex-1">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 sm:p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}