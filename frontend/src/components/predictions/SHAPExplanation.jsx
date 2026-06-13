import { InformationCircleIcon } from '@heroicons/react/24/outline';

export default function SHAPExplanation({ shapTopFeature, shapValue, probability }) {
  if (!shapTopFeature) return null;

  const impactColor = shapValue > 0 ? 'text-red-600' : 'text-green-600';
  const impactText = shapValue > 0 ? 'increases resistance risk' : 'decreases resistance risk';
  const baseProbability = probability < 0.1 ? 0.1 : (probability - shapValue).toFixed(3);

  return (
    <div className="mt-4 p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-100">
      <div className="flex items-start gap-3">
        <InformationCircleIcon className="h-5 w-5 text-primary-500 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-gray-800 mb-2">🔍 SHAP Explanation – Why this prediction?</h4>
          <p className="text-sm text-gray-600">
            The most influential feature is <span className="font-bold text-primary-600">{shapTopFeature.replace(/_/g, ' ')}</span>.
          </p>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${impactColor} bg-opacity-10 bg-gray-100`}>
              Impact: {shapValue > 0 ? '+' : ''}{shapValue.toFixed(3)}
            </span>
            <span className="text-xs text-gray-500">
              This feature {impactText} by {Math.abs(shapValue).toFixed(3)} units.
            </span>
          </div>
          <div className="mt-3 w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${shapValue > 0 ? 'bg-red-500' : 'bg-green-500'}`}
              style={{ width: `${Math.min(Math.abs(shapValue) * 20, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            * SHAP values show how each feature pushes the prediction from the base probability (~{((1-probability)*100).toFixed(1)}%) to the final {((probability)*100).toFixed(1)}%.
          </p>
        </div>
      </div>
    </div>
  );
}