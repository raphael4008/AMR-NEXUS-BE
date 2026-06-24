import { useEffect, useState } from 'react';
import { LightBulbIcon } from '@heroicons/react/24/outline';
import api from '../../api/client';

export default function StewardshipTip({ result }) {
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    if (result?.mdr_flag && result.pathogen_code && result.antibiotic_class) {
      api.getRecommendations(result.pathogen_code, result.antibiotic_class).then(setRecommendation);
    }
  }, [result]);

  if (!recommendation || recommendation.alternative === 'No alternative found') return null;

  return (
    <div className="mt-4 p-4 bg-blue-50/80 backdrop-blur-sm rounded-2xl border border-blue-200 shadow-sm transition-all hover:shadow-md">
      <div className="flex items-start gap-3">
        <LightBulbIcon className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-blue-800 flex items-center gap-2">
            <LightBulbIcon className="h-4 w-4 text-blue-500" />
            Stewardship Recommendation
          </h4>
          <p className="text-sm text-blue-700 mt-1">
            Consider <strong className="font-semibold">{recommendation.alternative}</strong>{' '}
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full ml-1">
              {recommendation.probability}% susceptibility
            </span>
          </p>
          {recommendation.note && (
            <p className="text-xs text-blue-600 mt-2 border-t border-blue-100 pt-2">
              <span className="font-medium">Note:</span> {recommendation.note}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}