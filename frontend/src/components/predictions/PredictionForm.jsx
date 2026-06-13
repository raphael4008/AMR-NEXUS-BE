import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { pathogens, counties } from '../../utils/constants';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useBarcodeScanner } from '../../hooks/useBarcodeScanner';
import { useOfflineDrafts } from '../../hooks/useOfflineDrafts';

const schema = z.object({
  sector: z.enum(['HUMAN', 'ANIMAL', 'ENVIRONMENT']),
  sub_sector: z.string().min(1),
  pathogen_code: z.string().min(1),
  specimen_type: z.string().min(1),
  county: z.string().min(1),
  antibiotic_class: z.string().min(1),
  test_method: z.string().min(1),
  sample_month: z.number().min(1).max(12),
  isolate_id: z.string().optional(),
  prior_antibiotic_exposure: z.boolean().optional(),
  age_group: z.string().optional(),
  gender: z.string().optional(),
  hospitalised: z.boolean().optional(),
  facility: z.string().optional(),
});

const PredictionForm = forwardRef(({ onSubmit, isLoading }, ref) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      sector: 'ANIMAL',
      sub_sector: 'Poultry-Broiler',
      pathogen_code: 'eco',
      specimen_type: 'Cloacal swab',
      county: 'Nairobi',
      antibiotic_class: 'Fluoroquinolone',
      test_method: 'Disk diffusion',
      sample_month: new Date().getMonth() + 1,
      isolate_id: '',
      prior_antibiotic_exposure: false,
      hospitalised: false,
      facility: '',
    },
  });

  const { isListening, transcript, startListening } = useSpeechRecognition();
  const { code, startScan } = useBarcodeScanner();
  const { addDraft } = useOfflineDrafts();

  // Expose setValues for parent (DraftsManager)
  useImperativeHandle(ref, () => ({
    setValues: (data) => {
      Object.keys(data).forEach(key => setValue(key, data[key]));
    }
  }));

  // Speech-to-text: fill facility field
  useEffect(() => {
    if (transcript) setValue('facility', transcript);
  }, [transcript, setValue]);

  // Barcode: fill isolate_id field
  useEffect(() => {
    if (code) setValue('isolate_id', code);
  }, [code, setValue]);

  // Auto-save draft every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      const formData = watch();
      if (Object.keys(formData).length) {
        addDraft({ formData, timestamp: new Date() });
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [watch, addDraft]);

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6 max-h-[80vh] overflow-y-auto">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">New AMR Prediction</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sector */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Sector *</label>
            <select {...register('sector')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500/20">
              <option value="HUMAN">Human</option>
              <option value="ANIMAL">Animal</option>
              <option value="ENVIRONMENT">Environment</option>
            </select>
          </div>
          {/* Sub-sector */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Sub-sector *</label>
            <input {...register('sub_sector')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" placeholder="e.g., Poultry-Broiler" />
            {errors.sub_sector && <p className="text-red-500 text-xs mt-1">{errors.sub_sector.message}</p>}
          </div>
          {/* Pathogen */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Pathogen *</label>
            <select {...register('pathogen_code')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm">
              {Object.entries(pathogens).map(([code, name]) => (<option key={code} value={code}>{name}</option>))}
            </select>
          </div>
          {/* Specimen Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Specimen Type *</label>
            <input {...register('specimen_type')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" />
          </div>
          {/* County */}
          <div>
            <label className="block text-sm font-medium text-gray-700">County *</label>
            <select {...register('county')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm">
              {counties.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          {/* Antibiotic Class */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Antibiotic Class *</label>
            <select {...register('antibiotic_class')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm">
              <option>Fluoroquinolone</option><option>Penicillin</option><option>Aminoglycoside</option>
              <option>Carbapenem</option><option>Tetracycline</option><option>Macrolide</option><option>Cephalosporin</option>
            </select>
          </div>
          {/* Test Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Test Method *</label>
            <input {...register('test_method')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" />
          </div>
          {/* Sample Month */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Sample Month *</label>
            <input type="number" {...register('sample_month', { valueAsNumber: true })} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" min="1" max="12" />
          </div>
          {/* Isolate ID (new) */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Isolate ID</label>
            <div className="flex gap-2">
              <input {...register('isolate_id')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" placeholder="Scan or enter ID" />
              <button type="button" onClick={startScan} className="mt-1 px-3 py-2 bg-gray-200 rounded-full text-xs">?? Scan</button>
            </div>
          </div>
        </div>

        {/* Advanced toggle */}
        <button type="button" onClick={() => setShowAdvanced(!showAdvanced)} className="text-sm text-primary-600 hover:text-primary-700">
          {showAdvanced ? '- Hide advanced' : '+ Show advanced'}
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-100">
            <label className="flex items-center gap-2"><input type="checkbox" {...register('prior_antibiotic_exposure')} className="rounded border-gray-300" /><span className="text-sm">Prior antibiotic exposure (30d)</span></label>
            <label className="flex items-center gap-2"><input type="checkbox" {...register('hospitalised')} className="rounded border-gray-300" /><span className="text-sm">Hospitalised</span></label>
            <div><label className="block text-sm">Age group</label><input {...register('age_group')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" /></div>
            <div><label className="block text-sm">Gender</label><select {...register('gender')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm"><option value="">Unknown</option><option value="M">Male</option><option value="F">Female</option></select></div>
            <div className="md:col-span-2">
              <label className="block text-sm">Facility</label>
              <div className="flex gap-2">
                <input {...register('facility')} className="mt-1 block w-full rounded-full border-gray-200 bg-gray-50/50 px-4 py-2 text-sm" placeholder="Enter facility name" />
                <button type="button" onClick={startListening} disabled={isListening} className="mt-1 px-3 py-2 bg-gray-200 rounded-full text-xs">
                  {isListening ? '?? Listening...' : '?? Speak'}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="pt-4">
          <button type="submit" disabled={isLoading} className="w-full md:w-auto px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-full shadow-sm transition-all disabled:opacity-50">
            {isLoading ? (<span className="flex items-center justify-center gap-2"><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Analysing...</span>) : 'Predict MDR'}
          </button>
        </div>
      </form>
    </div>
  );
});

PredictionForm.displayName = 'PredictionForm';
export default PredictionForm;
