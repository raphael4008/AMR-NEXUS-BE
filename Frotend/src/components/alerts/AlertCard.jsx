import { useState, useEffect } from 'react';
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import api from '../../api/client';

export default function AlertCard({
  alert,
  onAcknowledge,
  onDismiss,
  onToggleGuidance,
  isExpanded,
  guidance,
}) {
  const [isAcknowledged, setIsAcknowledged] = useState(alert.is_read || alert.acknowledged || false);
  const [localGuidance, setLocalGuidance] = useState(guidance);
  const [loadingGuidance, setLoadingGuidance] = useState(false);

  const isRead = alert.is_read !== undefined ? alert.is_read : alert.acknowledged;
  const severity = inferSeverity(alert.message);
  const severityColors = {
    high: 'border-l-red-500 bg-red-50/50',
    medium: 'border-l-yellow-500 bg-yellow-50/50',
    low: 'border-l-blue-500 bg-blue-50/50',
  };
  const severityBadge = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-blue-100 text-blue-800',
  };

  function inferSeverity(message) {
    const msg = (message || '').toLowerCase();
    if (msg.includes('critical') || msg.includes('high') || msg.includes('spike') || msg.includes('severe')) {
      return 'high';
    }
    if (msg.includes('warning') || msg.includes('medium') || msg.includes('alert')) {
      return 'medium';
    }
    return 'low';
  }

  const handleAcknowledge = async () => {
    if (isRead) return;
    try {
      await api.markAlertRead(alert.id);
      setIsAcknowledged(true);
      if (onAcknowledge) onAcknowledge(alert.id);
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleDismiss = async () => {
    try {
      await api.markAlertRead(alert.id);
      setIsAcknowledged(true);
      if (onDismiss) onDismiss(alert.id);
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const handleToggleGuidance = async () => {
    if (onToggleGuidance) {
      onToggleGuidance();
      return;
    }
    if (!isExpanded && alert.record_id) {
      setLoadingGuidance(true);
      try {
        const data = await api.getGuidanceForAlert(alert.record_id);
        setLocalGuidance(data.guidance);
      } catch (err) {
        console.error('Failed to fetch guidance:', err);
        setLocalGuidance('Guidance not available.');
      } finally {
        setLoadingGuidance(false);
      }
    }
  };

  const displayGuidance = guidance || localGuidance;

  return (
    <div
      className={`bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border-l-4 overflow-hidden transition-all ${
        severityColors[severity]
      } ${isRead ? 'opacity-60' : ''}`}
    >
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${severityBadge[severity]}`}>
                {severity === 'high' ? 'Critical' : severity === 'medium' ? 'Warning' : 'Info'}
              </span>
              <span className="text-xs text-gray-400">{new Date(alert.timestamp || alert.created_at).toLocaleString()}</span>
              {isRead && (
                <span className="text-xs text-green-600 flex items-center gap-1">
                  <CheckCircleIcon className="h-3 w-3" /> Acknowledged
                </span>
              )}
            </div>
            <p className="text-gray-800 font-medium">{alert.message}</p>
            {alert.details && <p className="text-sm text-gray-500 mt-1">{alert.details}</p>}
            {alert.shap_summary && (
              <p className="text-xs text-gray-600 mt-2 bg-gray-50 p-2 rounded-lg border border-gray-100">
                <span className="font-semibold">SHAP:</span> {alert.shap_summary}
              </p>
            )}
            <button
              onClick={handleToggleGuidance}
              className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
            >
              {isExpanded ? 'Hide guidance' : 'Show guidance'}
            </button>
            {isExpanded && displayGuidance && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-gray-700 whitespace-pre-wrap">
                {displayGuidance}
              </div>
            )}
            {isExpanded && loadingGuidance && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-500">Loading guidance...</div>
            )}
          </div>
          <div className="flex gap-2 ml-4">
            {!isRead && (
              <button
                onClick={handleAcknowledge}
                className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full hover:bg-primary-200"
              >
                Acknowledge
              </button>
            )}
            <button
              onClick={handleDismiss}
              className="text-gray-400 hover:text-gray-600"
              title="Dismiss"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}