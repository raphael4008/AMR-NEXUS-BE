import { useState, useEffect, useRef } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { DocumentDuplicateIcon, CloudArrowDownIcon } from '@heroicons/react/24/outline';
import PredictionForm from '../components/predictions/PredictionForm';
import ResultCard from '../components/predictions/ResultCard';
import StewardshipTip from '../components/predictions/StewardshipTip';
import DuplicateWarning from '../components/predictions/DuplicateWarning';
import HistorySidebar from '../components/predictions/HistorySidebar';
import DraftsManager from '../components/predictions/DraftsManager';
import TemplateSelector from '../components/predictions/TemplateSelector';
import BatchPredictUploader from '../components/predictions/BatchPredictUploader';
import api from '../api/client';
import { isDuplicate } from '../utils/duplicateDetection';
import { useOfflineDrafts } from '../hooks/useOfflineDrafts';

export default function Predict() {
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [recentPredictions, setRecentPredictions] = useState([]);
  const [currentFormData, setCurrentFormData] = useState(null);
  const formRef = useRef(null);
  const { addDraft } = useOfflineDrafts();

  useEffect(() => {
    api.getPredictions(20, 0).then(setRecentPredictions);
  }, []);

  const handleSubmit = async (formData) => {
    const dup = isDuplicate(formData, recentPredictions);
    if (dup && !window.confirm('Possible duplicate record. Continue anyway?')) return;
    setDuplicateWarning(dup);

    setIsLoading(true);
    try {
      const result = await api.submitPrediction(formData);
      setCurrentResult(result);
      toast.success('Prediction completed!');
      api.getPredictions(20, 0).then(setRecentPredictions);
    } catch (error) {
      toast.error(error.message || 'Prediction failed');
      if (!navigator.onLine) {
        await addDraft({ formData, timestamp: new Date() });
        toast(
          <div className="flex items-center gap-2">
            <CloudArrowDownIcon className="h-4 w-4 text-blue-500" />
            <span>Saved as offline draft</span>
          </div>,
          { duration: 4000 }
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadDraft = (data) => {
    formRef.current?.setValues(data);
    setCurrentFormData(data);
  };

  const handleLoadTemplate = (data) => {
    formRef.current?.setValues(data);
    setCurrentFormData(data);
  };

  const handleHistorySelect = (prediction) => {
    toast(
      <div className="flex items-center gap-2">
        <DocumentDuplicateIcon className="h-4 w-4 text-primary-600" />
        <span>Loaded prediction from {new Date(prediction.timestamp).toLocaleDateString()}</span>
      </div>,
      { duration: 3000 }
    );
  };

  const handleFormChange = (data) => {
    setCurrentFormData(data);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Toaster position="top-right" toastOptions={{ className: 'bg-white/80 backdrop-blur-sm rounded-full shadow-lg' }} />
      <div className="lg:col-span-2 space-y-4">
        <TemplateSelector
          onLoadTemplate={handleLoadTemplate}
          currentFormData={currentFormData}
        />
        <DraftsManager onLoadDraft={handleLoadDraft} onSubmitDraft={handleSubmit} />
        <PredictionForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          ref={formRef}
          onFormChange={handleFormChange}
        />
        {duplicateWarning && <DuplicateWarning duplicate={duplicateWarning} />}
        {currentResult && <ResultCard result={currentResult} />}
        {currentResult && <StewardshipTip result={currentResult} />}
        <BatchPredictUploader onBatchComplete={(outcomes) => {
          const successCount = outcomes.filter(o => o.success).length;
          toast.success(`${successCount} of ${outcomes.length} predictions submitted.`);
          api.getPredictions(20, 0).then(setRecentPredictions);
        }} />
      </div>
      <div>
        <HistorySidebar onSelect={handleHistorySelect} />
      </div>
    </div>
  );
}