import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const predictionSchema = z.object({
  sector: z.enum(['HUMAN', 'ANIMAL', 'ENVIRONMENT']),
  sub_sector: z.string().min(1),
  pathogen_code: z.string().min(1),
  specimen_type: z.string().min(1),
  county: z.string().min(1),
  antibiotic_class: z.string().min(1),
  test_method: z.string().min(1),
  sample_month: z.number().min(1).max(12),
  prior_antibiotic_exposure: z.boolean().optional(),
  age_group: z.string().optional(),
  gender: z.string().optional(),
  hospitalised: z.boolean().optional(),
  facility: z.string().optional(),
});

export default function PredictionForm({ onSubmit, isLoading = false }) {   // renamed prop to "isLoading" with default
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(predictionSchema),
    defaultValues: {
      sector: 'ANIMAL',
      sub_sector: 'Poultry-Broiler',
      pathogen_code: 'eco',
      specimen_type: 'Cloacal swab',
      county: 'Nairobi',
      antibiotic_class: 'Fluoroquinolones',
      test_method: 'Disk diffusion',
      sample_month: new Date().getMonth() + 1,
      prior_antibiotic_exposure: false,
      hospitalised: false,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sector */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Sector *</label>
          <select {...register('sector')} className="input mt-1 w-full">
            <option value="HUMAN">Human</option>
            <option value="ANIMAL">Animal</option>
            <option value="ENVIRONMENT">Environment</option>
          </select>
        </div>

        {/* Sub-sector */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Sub‑sector *</label>
          <input {...register('sub_sector')} className="input mt-1 w-full" placeholder="e.g., Poultry-Broiler" />
          {errors.sub_sector && <p className="text-red-500 text-xs mt-1">{errors.sub_sector.message}</p>}
        </div>

        {/* Pathogen Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Pathogen Code *</label>
          <select {...register('pathogen_code')} className="input mt-1 w-full">
            <option value="eco">E. coli (eco)</option>
            <option value="kpn">K. pneumoniae (kpn)</option>
            <option value="sau">S. aureus (sau)</option>
            <option value="sal">Salmonella spp. (sal)</option>
            <option value="cam">C. jejuni (cam)</option>
            <option value="pae">P. aeruginosa (pae)</option>
            <option value="aba">A. baumannii (aba)</option>
            <option value="efc">E. faecalis (efc)</option>
            <option value="spn">S. pneumoniae (spn)</option>
            <option value="ecl">E. cloacae (ecl)</option>
          </select>
        </div>

        {/* Specimen Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Specimen Type *</label>
          <input {...register('specimen_type')} className="input mt-1 w-full" placeholder="e.g., Blood, Urine, Swab" />
        </div>

        {/* County */}
        <div>
          <label className="block text-sm font-medium text-gray-700">County *</label>
          <input {...register('county')} className="input mt-1 w-full" placeholder="e.g., Nairobi" />
        </div>

        {/* Antibiotic Class */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Antibiotic Class *</label>
          <select {...register('antibiotic_class')} className="input mt-1 w-full">
            <option value="Fluoroquinolone">Fluoroquinolone</option>
            <option value="Penicillin">Penicillin</option>
            <option value="Aminoglycoside">Aminoglycoside</option>
            <option value="Carbapenem">Carbapenem</option>
            <option value="Tetracycline">Tetracycline</option>
            <option value="Macrolide">Macrolide</option>
            <option value="Cephalosporin">Cephalosporin</option>
          </select>
        </div>

        {/* Test Method */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Test Method *</label>
          <input {...register('test_method')} className="input mt-1 w-full" placeholder="e.g., Disk diffusion" />
        </div>

        {/* Sample Month */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Sample Month *</label>
          <input type="number" {...register('sample_month', { valueAsNumber: true })} className="input mt-1 w-full" min="1" max="12" />
        </div>

        {/* Prior Antibiotic Exposure */}
        <div className="flex items-center">
          <input type="checkbox" {...register('prior_antibiotic_exposure')} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
          <label className="ml-2 block text-sm text-gray-700">Prior antibiotic exposure (last 30 days)</label>
        </div>

        {/* Hospitalised */}
        <div className="flex items-center">
          <input type="checkbox" {...register('hospitalised')} className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded" />
          <label className="ml-2 block text-sm text-gray-700">Hospitalised</label>
        </div>

        {/* Gender */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Gender</label>
          <select {...register('gender')} className="input mt-1 w-full">
            <option value="">Unknown</option>
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
        </div>

        {/* Age Group */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Age Group</label>
          <input {...register('age_group')} className="input mt-1 w-full" placeholder="e.g., Adult, Child, 60+ years" />
        </div>

        {/* Facility */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">Facility (optional)</label>
          <input {...register('facility')} className="input mt-1 w-full" placeholder="e.g., Kenyatta National Hospital" />
        </div>
      </div>

      {/* SUBMIT BUTTON - made more visible */}
      <div className="flex justify-start pt-4">
        <button
          type="submit"
          disabled={isLoading}
          className="px-8 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analysing...
            </>
          ) : (
            'Predict MDR'
          )}
        </button>
      </div>
    </form>
  );
}