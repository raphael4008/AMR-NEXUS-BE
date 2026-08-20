import { useEffect, useState } from 'react';
import { LightBulbIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const API_BASE = 'http://localhost:8000';

export default function AlertGuidance({
  alert,
  userRole = 'county',
  county = '',
  onGuidanceLoaded = null,
}) {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchGuidance = async () => {
    if (!alert?.pathogen_code) {
      setError('No pathogen information available.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/guidance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pathogen_code: alert.pathogen_code,
          resistance_pattern: alert.resistance_pattern || 'ESBL',
          user_role: userRole || 'county',
          county: county || alert.county || '',
          antibiotic_class: alert.antibiotic_class || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setGuidance(data);
      if (onGuidanceLoaded) onGuidanceLoaded(data);
    } catch (err) {
      console.error('Failed to fetch guidance:', err);
      setError(err.message || 'Could not load guidance. Please try again.');
      toast.error('Failed to load guidance');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (alert?.pathogen_code) {
      fetchGuidance();
    }
  }, [alert?.pathogen_code, alert?.resistance_pattern, userRole, county, retryCount]);

  const handleRetry = () => {
    setRetryCount((prev) => prev + 1);
  };

  if (!alert?.pathogen_code) {
    return null;
  }

  return (
    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
      <div className="flex items-start gap-3">
        <LightBulbIcon className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="flex justify-between items-center mb-2">
            <h4 className="text-sm font-semibold text-blue-800">
              📋 Stewardship Guidance
            </h4>
            {!loading && !error && (
              <button
                onClick={fetchGuidance}
                className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                <ArrowPathIcon className="h-3 w-3" /> Refresh
              </button>
            )}
          </div>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              Loading guidance...
            </div>
          )}

          {error && (
            <div className="text-sm text-red-600">
              <p>{error}</p>
              <button
                onClick={handleRetry}
                className="mt-1 text-xs text-blue-600 underline hover:text-blue-800"
              >
                Retry
              </button>
            </div>
          )}

          {guidance && !loading && !error && (
            <>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">
                {guidance.guidance}
              </div>
              {guidance.source && (
                <p className="text-xs text-gray-400 mt-2">
                  Source: {guidance.source}
                </p>
              )}
              {guidance.recommendations && guidance.recommendations.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-gray-600">Recommendations:</p>
                  <ul className="list-disc list-inside text-xs text-gray-600 mt-1">
                    {guidance.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}