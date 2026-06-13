import { useState } from 'react';
import PredictionForm from '../components/predictions/PredictionForm';
import ResultCard from '../components/predictions/ResultCard';
import api from '../api/client';

export default function Compare() {
  const [left, setLeft] = useState(null);
  const [right, setRight] = useState(null);
  const [leftLoading, setLeftLoading] = useState(false);
  const [rightLoading, setRightLoading] = useState(false);

  const onSubmitLeft = async (data) => {
    setLeftLoading(true);
    const res = await api.submitPrediction(data);
    setLeft(res);
    setLeftLoading(false);
  };
  const onSubmitRight = async (data) => {
    setRightLoading(true);
    const res = await api.submitPrediction(data);
    setRight(res);
    setRightLoading(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <PredictionForm onSubmit={onSubmitLeft} isLoading={leftLoading} />
        {left && <ResultCard result={left} />}
      </div>
      <div>
        <PredictionForm onSubmit={onSubmitRight} isLoading={rightLoading} />
        {right && <ResultCard result={right} />}
      </div>
    </div>
  );
}
