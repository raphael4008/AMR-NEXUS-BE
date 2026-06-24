// src/components/predictions/SHAPExplanation.jsx
import Card from '../ui/Card';

export default function SHAPExplanation({ shapTopFeature, shapValue, probability }) {
  if (!shapTopFeature) return null;

  const impactColor = shapValue > 0 ? 'text-red-600' : 'text-green-600';
  const impactText = shapValue > 0 ? 'increases resistance risk' : 'decreases resistance risk';

  return (
    <Card className="mt-4">
      <h4 className="text-md font-semibold mb-2">🔍 SHAP Explanation</h4>
      <p className="text-sm text-gray-600">
        The most influential factor for this prediction is:
      </p>
      <div className="mt-2 p-3 bg-gray-50 rounded-lg">
        <span className="font-mono font-bold">{shapTopFeature.replace(/_/g, ' ')}</span>
        <span className={`ml-2 ${impactColor}`}>
          ({shapValue > 0 ? '+' : ''}{shapValue.toFixed(3)})
        </span>
        <p className="text-xs text-gray-500 mt-1">
          This feature {impactText} by {Math.abs(shapValue).toFixed(3)} units.
        </p>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        SHAP values show how each feature pushes the prediction from the base probability (≈{((1-probability)*100).toFixed(1)}%) to the final {((probability)*100).toFixed(1)}%.
      </p>
    </Card>
  );
}