import { useEffect, useState } from 'react';
import { LightBulbIcon } from '@heroicons/react/24/outline';

export default function AlertGuidance({ alert, userRole, county }) {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (alert?.pathogen_code && alert?.resistance_pattern) {
      setLoading(true);
      fetch('http://localhost:8000/guidance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pathogen_code: alert.pathogen_code,
          resistance_pattern: alert.resistance_pattern || 'ESBL',
          user_role: userRole || 'county',
          county: county
        })
      })
        .then(res => res.json())
        .then(data => {
          setGuidance(data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [alert]);

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