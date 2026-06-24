import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import Select from 'react-select';
import { QrCodeIcon, MicrophoneIcon } from '@heroicons/react/24/outline';
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

// Options for react-select
const sectorOptions = ['HUMAN', 'ANIMAL', 'ENVIRONMENT'].map(v => ({ value: v, label: v }));
const pathogenOptions = Object.entries(pathogens).map(([code, name]) => ({ value: code, label: `${name} (${code})` }));
const countyOptions = counties.map(c => ({ value: c, label: c }));
const antibioticOptions = ['Fluoroquinolone', 'Penicillin', 'Aminoglycoside', 'Carbapenem', 'Tetracycline', 'Macrolide', 'Cephalosporin'].map(v => ({ value: v, label: v }));
const testMethodOptions = ['Disk diffusion', 'MIC', 'Etest', 'Broth microdilution'].map(v => ({ value: v, label: v }));
const genderOptions = ['', 'M', 'F'].map(v => ({ value: v, label: v || 'Unknown' }));

const PredictionForm = forwardRef(({ onSubmit, isLoading, onFormChange }, ref) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { register, handleSubmit, setValue, watch, control, formState: { errors } } = useForm({
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

  const watchedValues = useWatch({ control });
  useEffect(() => {
    if (onFormChange) onFormChange(watchedValues);
  }, [watchedValues, onFormChange]);

  useImperativeHandle(ref, () => ({
    setValues: (data) => {
      Object.keys(data).forEach(key => setValue(key, data[key]));
    }
  }));

  useEffect(() => {
    if (transcript) setValue('facility', transcript);
  }, [transcript, setValue]);

  useEffect(() => {
    if (code) setValue('isolate_id', code);
  }, [code, setValue]);

  useEffect(() => {
    const interval = setInterval(() => {
      const formData = watch();
      if (Object.keys(formData).length) {
        addDraft({ formData, timestamp: new Date() });
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [watch, addDraft]);

  // React‑select styles with high contrast
  const selectStyles = {
    control: (base, state) => ({
      ...base,
      borderRadius: '9999px',
      borderColor: state.isFocused ? '#2563eb' : '#d1d5db',
      borderWidth: '2px',
      boxShadow: state.isFocused ? '0 0 0 3px rgba(37, 99, 235, 0.2)' : 'none',
      '&:hover': { borderColor: '#9ca3af' },
      minHeight: '42px',
      backgroundColor: '#ffffff',
    }),
    menu: (base) => ({
      ...base,
      borderRadius: '12px',
      marginTop: '4px',
      zIndex: 20,
      backgroundColor: '#ffffff',
      border: '1px solid #e5e7eb',
      boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
    }),
    option: (base, { isFocused, isSelected }) => ({
      ...base,
      backgroundColor: isSelected ? '#2563eb' : isFocused ? '#eff6ff' : '#ffffff',
      color: isSelected ? '#ffffff' : '#1f2937',
      padding: '8px 16px',
      cursor: 'pointer',
    }),
    menuPortal: (base) => ({ ...base, zIndex: 20 }),
    placeholder: (base) => ({ ...base, color: '#9ca3af' }),
    singleValue: (base) => ({ ...base, color: '#1f2937', fontWeight: 500 }),
    input: (base) => ({ ...base, color: '#1f2937' }),
  };

  // Helper to render react-select
  const renderSelect = (name, options, placeholder, isClearable = true) => (
    <Select
      options={options}
      value={options.find(o => o.value === watch(name)) || null}
      onChange={(opt) => setValue(name, opt?.value || '')}
      placeholder={placeholder}
      isClearable={isClearable}
      styles={selectStyles}
      menuPortalTarget={document.body}
    />
  );

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">New AMR Prediction</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Scrollable fields container */}
        <div className="max-h-[60vh] overflow-y-auto pr-2 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Sector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Sector *</label>
              {renderSelect('sector', sectorOptions, 'Select sector')}
            </div>
            {/* Sub-sector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Sub-sector *</label>
              <input {...register('sub_sector')} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" placeholder="e.g., Poultry-Broiler" />
              {errors.sub_sector && <p className="text-red-500 text-xs mt-1">{errors.sub_sector.message}</p>}
            </div>
            {/* Pathogen */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Pathogen *</label>
              {renderSelect('pathogen_code', pathogenOptions, 'Search pathogen...')}
            </div>
            {/* Specimen Type */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Specimen Type *</label>
              <input {...register('specimen_type')} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" />
            </div>
            {/* County */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">County *</label>
              {renderSelect('county', countyOptions, 'Search county...')}
            </div>
            {/* Antibiotic Class */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Antibiotic Class *</label>
              {renderSelect('antibiotic_class', antibioticOptions, 'Select antibiotic')}
            </div>
            {/* Test Method */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Test Method *</label>
              {renderSelect('test_method', testMethodOptions, 'Select method')}
            </div>
            {/* Sample Month */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Sample Month *</label>
              <input type="number" {...register('sample_month', { valueAsNumber: true })} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" min="1" max="12" />
            </div>
            {/* Isolate ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Isolate ID</label>
              <div className="flex gap-2">
                <input {...register('isolate_id')} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" placeholder="Scan or enter ID" />
                <button type="button" onClick={startScan} className="mt-1 inline-flex items-center gap-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-full text-sm font-medium text-gray-800 transition-colors">
                  <QrCodeIcon className="h-4 w-4" /> Scan
                </button>
              </div>
            </div>
          </div>

          {/* Advanced toggle */}
          <button type="button" onClick={() => setShowAdvanced(!showAdvanced)} className="text-sm font-medium text-primary-600 hover:text-primary-700">
            {showAdvanced ? '− Hide advanced' : '+ Show advanced'}
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-100">
              <label className="flex items-center gap-2"><input type="checkbox" {...register('prior_antibiotic_exposure')} className="rounded border-gray-300" /><span className="text-sm">Prior antibiotic exposure (30d)</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" {...register('hospitalised')} className="rounded border-gray-300" /><span className="text-sm">Hospitalised</span></label>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Age group</label>
                <input {...register('age_group')} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Gender</label>
                {renderSelect('gender', genderOptions, 'Select gender', true)}
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Facility</label>
                <div className="flex gap-2">
                  <input {...register('facility')} className="mt-1 block w-full rounded-full border-2 border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20" placeholder="Enter facility name" />
                  <button type="button" onClick={startListening} disabled={isListening} className="mt-1 inline-flex items-center gap-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-full text-sm font-medium text-gray-800 transition-colors disabled:opacity-50">
                    <MicrophoneIcon className={`h-4 w-4 ${isListening ? 'text-red-500 animate-pulse' : ''}`} />
                    {isListening ? 'Listening...' : 'Speak'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Submit button – always visible, outside scrollable area */}
        <div className="pt-4 border-t border-gray-100">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full md:w-auto px-10 py-3.5 bg-gray-900 hover:bg-gray-800 text-white font-bold text-lg rounded-full shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-gray-500 focus:ring-offset-2"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-3">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analysing...
              </span>
            ) : (
              'Predict MDR'
            )}
          </button>
        </div>
      </form>
    </div>
  );
});

PredictionForm.displayName = 'PredictionForm';
export default PredictionForm;