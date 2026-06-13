import Alert from '../ui/Alert';
import SHAPExplanation from './SHAPExplanation';

export default function ResultCard({ result }) {
  if (!result) return null;

  const { mdr_flag, mdr_probability, anomaly_detected, anomaly_score, shap_top_feature, shap_value } = result;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Prediction Outcome</h3>

      {/* MDR Status Card */}
      <div className={`p-4 rounded-xl mb-4 ${mdr_flag ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-700">MDR Status</span>
          <span className={`text-xl font-bold ${mdr_flag ? 'text-red-600' : 'text-green-600'}`}>
            {mdr_flag ? 'RESISTANT' : 'SUSCEPTIBLE'}
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div className={`h-2 rounded-full ${mdr_flag ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${mdr_probability * 100}%` }} />
        </div>
        <p className="text-sm text-gray-600 mt-1">Confidence: {(mdr_probability * 100).toFixed(1)}%</p>
      </div>

      {/* Anomaly Alert */}
      {anomaly_detected && (
        <Alert type="warning" className="mb-4">
          <strong>⚠️ Anomaly Detected</strong> – Unusual resistance pattern (score {anomaly_score.toFixed(3)}).
        </Alert>
      )}

      {/* SHAP Explanation (new) */}
      <SHAPExplanation shapTopFeature={shap_top_feature} shapValue={shap_value} probability={mdr_probability} />
    </div>
  );
}