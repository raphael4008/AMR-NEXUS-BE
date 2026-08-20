import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useNavigate } from 'react-router-dom';
import { 
  ExclamationTriangleIcon, 
  ShieldExclamationIcon, 
  InformationCircleIcon, 
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  BellAlertIcon
} from '@heroicons/react/24/outline';

const SOCKET_URL = 'http://localhost:8000';

export default function LiveAlertPopup() {
  const [toastAlerts, setToastAlerts] = useState([]);
  const [isSurgeExpanded, setIsSurgeExpanded] = useState(false);
  const recentIdsRef = useRef(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    const socket = io(SOCKET_URL);

    socket.on('amr_alert', (alertData) => {
      const alertId = alertData.id || `alert-${Date.now()}`;

      // 1. DEDUPLICATION CHECK: Ignore if identical ID arrived in the last 10 seconds
      if (recentIdsRef.current.has(alertId)) {
        return;
      }
      recentIdsRef.current.add(alertId);
      setTimeout(() => {
        recentIdsRef.current.delete(alertId);
      }, 10000);

      const uniqueKey = `${alertId}-${Date.now()}`;
      const newAlert = { ...alertData, uniqueId: uniqueKey, id: alertId };

      setToastAlerts((prev) => {
        // 2. SURGE PROTECTION & BATCHING: 
        // If more than 4 active toasts are already showing, treat incoming as a burst surge
        const updated = alertData.severity === 'critical' ? [newAlert, ...prev] : [...prev, newAlert];
        return updated;
      });

      // Auto-dismiss logic for non-critical alerts
      if (alertData.severity !== 'critical') {
        const duration = alertData.severity === 'high' ? 10000 : 4000;
        setTimeout(() => {
          setToastAlerts((prev) => prev.filter((t) => t.uniqueId !== uniqueKey));
        }, duration);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const handleDismissToast = (uniqueId, e) => {
    e.stopPropagation(); // Prevent triggering deep-link navigation
    setToastAlerts((prev) => prev.filter((t) => t.uniqueId !== uniqueId));
  };

  // 3. ACTIONABLE DEEP-LINKING: Clicking an alert dismisses it and navigates to the alerts view
  const handleAlertClick = (alert) => {
    // Remove the clicked alert immediately so it disappears
    setToastAlerts((prev) => prev.filter((t) => t.uniqueId !== alert.uniqueId));
    
    // Navigate to the alerts view
    navigate('/alerts', { state: { highlightId: alert.id, county: alert.county } });
  };

  // Separate critical/high items from surge grouping if there are too many
  const criticalOrHighAlerts = toastAlerts.filter(t => t.severity === 'critical' || t.severity === 'high');
  const normalAlerts = toastAlerts.filter(t => t.severity !== 'critical' && t.severity !== 'high');
  const isSurgeCondition = toastAlerts.length > 4;

  return (
    <div className="fixed top-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none">
      
      {/* SURGE BATCHING CARD (Triggered if active alerts exceed 4) */}
      {isSurgeCondition && !isSurgeExpanded && (
        <div 
          onClick={() => setIsSurgeExpanded(true)}
          className="pointer-events-auto cursor-pointer bg-gradient-to-r from-red-600 to-amber-600 text-white p-4 rounded-2xl shadow-2xl flex items-center justify-between animate-bounce-subtle"
        >
          <div className="flex items-center gap-3">
            <BellAlertIcon className="h-6 w-6 animate-pulse" />
            <div>
              <p className="text-sm font-bold">Surge Alert Detected</p>
              <p className="text-xs text-white/90">{toastAlerts.length} active notifications streaming in.</p>
            </div>
          </div>
          <ChevronDownIcon className="h-5 w-5" />
        </div>
      )}

      {/* SURGE EXPANDED VIEW OR NORMAL TOAST STACK */}
      {(!isSurgeCondition || isSurgeExpanded) && toastAlerts.map((alert) => {
        const isCritical = alert.severity === 'critical';
        const isHigh = alert.severity === 'high';

        return (
          <div
            key={alert.uniqueId}
            onClick={() => handleAlertClick(alert)}
            className={`pointer-events-auto cursor-pointer transform transition-all duration-300 ease-out shadow-2xl rounded-2xl border-l-4 p-4 backdrop-blur-md bg-white/95 hover:scale-[1.02] animate-slide-in ${
              isCritical
                ? 'border-l-red-600 ring-2 ring-red-500/20 shadow-red-500/10'
                : isHigh
                ? 'border-l-amber-500'
                : 'border-l-blue-500'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                {isCritical ? (
                  <ShieldExclamationIcon className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5 animate-pulse" />
                ) : isHigh ? (
                  <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <InformationCircleIcon className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        isCritical
                          ? 'bg-red-100 text-red-800'
                          : isHigh
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 mt-1">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {alert.county} County • Click to inspect
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => handleDismissToast(alert.uniqueId, e)}
                className="text-gray-400 hover:text-gray-600 transition p-1 rounded-lg hover:bg-gray-100"
                title="Dismiss alert"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Auto-dismiss progress bar for High & Medium only */}
            {!isCritical && !isSurgeCondition && (
              <div className="w-full bg-gray-100 h-1 rounded-full mt-3 overflow-hidden">
                <div
                  className={`h-full ${isHigh ? 'bg-amber-500' : 'bg-blue-500'} animate-countdown`}
                  style={{ animationDuration: isHigh ? '10s' : '4s' }}
                ></div>
              </div>
            )}
          </div>
        );
      })}

      {/* Collapse button if surge was expanded */}
      {isSurgeCondition && isSurgeExpanded && (
        <button
          onClick={() => setIsSurgeExpanded(false)}
          className="pointer-events-auto bg-gray-800 text-white text-xs py-2 rounded-xl shadow-lg flex items-center justify-center gap-1 hover:bg-gray-900 transition"
        >
          <ChevronUpIcon className="h-4 w-4" /> Collapse Surge Stack
        </button>
      )}
    </div>
  );
}