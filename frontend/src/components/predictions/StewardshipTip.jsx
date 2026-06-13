import { useEffect, useState } from 'react';
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
    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl">
      <p className="text-sm font-medium text-blue-800">💊 Stewardship Recommendation</p>
      <p className="text-sm text-blue-700">Consider <strong>{recommendation.alternative}</strong> (estimated susceptibility {recommendation.probability}%)</p>
      <p className="text-xs text-blue-600 mt-1">{recommendation.note}</p>
    </div>
  );
}