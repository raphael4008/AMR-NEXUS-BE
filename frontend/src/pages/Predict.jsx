import { useState, useEffect, useRef } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import PredictionForm from '../components/predictions/PredictionForm';
import ResultCard from '../components/predictions/ResultCard';
import StewardshipTip from '../components/predictions/StewardshipTip';
import DuplicateWarning from '../components/predictions/DuplicateWarning';
import HistorySidebar from '../components/predictions/HistorySidebar';
import DraftsManager from '../components/predictions/DraftsManager';
import TemplateSelector from '../components/predictions/TemplateSelector';
import api from '../api/client';
import { isDuplicate } from '../utils/duplicateDetection';
import { useOfflineDrafts } from '../hooks/useOfflineDrafts';

export default function Predict() {
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [recentPredictions, setRecentPredictions] = useState([]);
  const formRef = useRef(null);
  const { addDraft } = useOfflineDrafts();

  useEffect(() => {
    api.getPredictions(20, 0).then(setRecentPredictions);
  }, []);

  const handleSubmit = async (formData) => {
    // Check duplicate
    const dup = isDuplicate(formData, recentPredictions);
    if (dup && !window.confirm('Possible duplicate record. Continue anyway?')) return;
    setDuplicateWarning(dup);

    setIsLoading(true);
    try {
      const result = await api.submitPrediction(formData);
      setCurrentResult(result);
      toast.success('Prediction completed!');
      // Refresh recent list
      api.getPredictions(20, 0).then(setRecentPredictions);
      // Remove any draft for this data (optional)
    } catch (error) {
      toast.error(error.message || 'Prediction failed');
      // Save as draft if offline
      if (!navigator.onLine) {
        await addDraft({ formData, timestamp: new Date() });
        toast.info('Saved as offline draft');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadDraft = (data) => {
    formRef.current?.setValues(data);
  };

  const handleLoadTemplate = (data) => {
    formRef.current?.setValues(data);
  };

  const handleHistorySelect = (prediction) => {
    // Could prefill form, but we just show a toast
    toast(`Loaded prediction from ${new Date(prediction.timestamp).toLocaleDateString()}`, { icon: '📋' });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Toaster position="top-right" />
      <div className="lg:col-span-2 space-y-4">
        <TemplateSelector onLoadTemplate={handleLoadTemplate} />
        <DraftsManager onLoadDraft={handleLoadDraft} onSubmitDraft={handleSubmit} />
        <PredictionForm onSubmit={handleSubmit} isLoading={isLoading} ref={formRef} />
        {duplicateWarning && <DuplicateWarning duplicate={duplicateWarning} />}
        {currentResult && <ResultCard result={currentResult} />}
        {currentResult && <StewardshipTip result={currentResult} />}
      </div>
      <div>
        <HistorySidebar onSelect={handleHistorySelect} />
      </div>
    </div>
  );
}