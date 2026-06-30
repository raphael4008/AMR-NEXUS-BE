import { useState } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import PredictionForm from '../components/predictions/PredictionForm';
import ResultCard from '../components/predictions/ResultCard';
import api from '../api/client';

export default function Compare() {
  const [left, setLeft]           = useState(null);
  const [right, setRight]         = useState(null);
  const [leftLoading, setLeftLoading]   = useState(false);
  const [rightLoading, setRightLoading] = useState(false);

  const onSubmitLeft = async (data) => {
    setLeftLoading(true);
    try {
      const res = await api.submitPrediction(data);
      // submitPrediction → bulkIngest → returns { ingested, records[] }
      // ResultCard expects a single prediction object, so use the first record
      const record = Array.isArray(res.data?.records) ? res.data.records[0] : res.data;
      setLeft(record ?? null);
    } catch (err) {
      toast.error('Left prediction failed: ' + (err.response?.data?.detail ?? err.message));
    } finally {
      setLeftLoading(false);
    }
  };

  const onSubmitRight = async (data) => {
    setRightLoading(true);
    try {
      const res = await api.submitPrediction(data);
      const record = Array.isArray(res.data?.records) ? res.data.records[0] : res.data;
      setRight(record ?? null);
    } catch (err) {
      toast.error('Right prediction failed: ' + (err.response?.data?.detail ?? err.message));
    } finally {
      setRightLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Toaster position="top-right" />
      <h1 className="text-2xl font-bold text-gray-900">Side-by-Side Comparison</h1>
      <p className="text-sm text-gray-500">Submit two different records to compare their MDR predictions.</p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-gray-700 border-b pb-2">Record A</h2>
          <PredictionForm onSubmit={onSubmitLeft} isLoading={leftLoading} />
          {left && <ResultCard result={left} />}
        </div>
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-gray-700 border-b pb-2">Record B</h2>
          <PredictionForm onSubmit={onSubmitRight} isLoading={rightLoading} />
          {right && <ResultCard result={right} />}
        </div>
      </div>
    </div>
  );
}
