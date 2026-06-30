import { useEffect, useState } from 'react';
import { LightBulbIcon } from '@heroicons/react/24/outline';
import api from '../../api/client';

export default function AlertGuidance({ alert, userRole, county }) {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Only call decision-support if we have a real alert id
    if (!alert?.id) return;
    setLoading(true);
    api.triggerDecisionSupport(alert.id)
      .then(res => {
        setGuidance(res.data ?? null);
      })
      .catch(err => {
        console.warn('[AlertGuidance] decision-support unavailable:', err?.response?.status ?? err.message);
      })
      .finally(() => setLoading(false));
  }, [alert?.id]);

  if (!guidance) return null;

  return (
    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
      <div className="flex items-start gap-3">
        <LightBulbIcon className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-blue-800 mb-2">
            📋 Stewardship Guidance
          </h4>
          {loading ? (
            <p className="text-sm text-gray-500">Loading guidance...</p>
          ) : (
            <>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">
                {guidance.guidance}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Source: {guidance.source}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}