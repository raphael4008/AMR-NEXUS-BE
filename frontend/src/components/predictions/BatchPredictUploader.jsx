import { useState } from 'react';
import * as XLSX from 'xlsx';
import {
  CloudArrowUpIcon,
  DocumentArrowUpIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  PencilSquareIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import api from '../../api/client';
import { useOfflineDrafts } from '../../hooks/useOfflineDrafts';

const FIELDS = [
  { key: 'sector', label: 'Sector', required: false, default: 'ANIMAL' },
  { key: 'sub_sector', label: 'Sub-sector', required: false, default: 'Poultry-Broiler' },
  { key: 'pathogen_code', label: 'Pathogen', required: true, default: 'eco' },
  { key: 'specimen_type', label: 'Specimen Type', required: false, default: 'Swab' },
  { key: 'county', label: 'County', required: true, default: 'Nairobi' },
  { key: 'antibiotic_class', label: 'Antibiotic Class', required: true, default: 'Fluoroquinolone' },
  { key: 'test_method', label: 'Test Method', required: false, default: 'Disk diffusion' },
  { key: 'sample_month', label: 'Sample Month', required: false, default: 6 },
  { key: 'isolate_id', label: 'Isolate ID', required: false, default: '' },
  { key: 'prior_antibiotic_exposure', label: 'Prior Exposure', required: false, default: false },
  { key: 'age_group', label: 'Age Group', required: false, default: '' },
  { key: 'gender', label: 'Gender', required: false, default: '' },
  { key: 'hospitalised', label: 'Hospitalised', required: false, default: false },
  { key: 'facility', label: 'Facility', required: false, default: '' },
];

export default function BatchPredictUploader({ onBatchComplete }) {
  const [file, setFile] = useState(null);
  const [rows, setRows] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ processed: 0, total: 0 });
  const [columnMapping, setColumnMapping] = useState({});
  const [showMapping, setShowMapping] = useState(false);
  const { addDraft } = useOfflineDrafts();

  const detectColumns = (headers) => {
    const mapping = {};
    const usedColumns = new Set();
    FIELDS.forEach(field => {
      const match = headers.find(h =>
        !usedColumns.has(h) &&
        (h.toLowerCase() === field.key.toLowerCase() ||
         h.toLowerCase().replace(/[^a-z0-9]/g, '') === field.key.toLowerCase())
      );
      mapping[field.key] = match || '';
      if (match) usedColumns.add(match);
    });
    return mapping;
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFile(file);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json(sheet);
      setRows(json);
      setResults([]);
      setProgress({ processed: 0, total: 0 });
      const headers = Object.keys(json[0] || {});
      const mapping = detectColumns(headers);
      setColumnMapping(mapping);
      setShowMapping(true);
    };
    reader.readAsArrayBuffer(file);
  };

  const clearFile = () => {
    setFile(null);
    setRows([]);
    setResults([]);
    setProgress({ processed: 0, total: 0 });
    setColumnMapping({});
    setShowMapping(false);
  };

  const getRowValue = (row, fieldKey) => {
    const colName = columnMapping[fieldKey];
    if (!colName) {
      const field = FIELDS.find(f => f.key === fieldKey);
      return field?.default || '';
    }
    const val = row[colName];
    return val !== undefined && val !== null ? val : FIELDS.find(f => f.key === fieldKey)?.default || '';
  };

  const handleBatchSubmit = async () => {
    if (rows.length === 0) return;
    setProcessing(true);
    const total = rows.length;
    setProgress({ processed: 0, total });
    const outcomes = [];

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      try {
        const payload = {};
        FIELDS.forEach(field => {
          let val = getRowValue(row, field.key);
          if (field.key === 'sample_month') val = parseInt(val) || field.default;
          if (field.key === 'prior_antibiotic_exposure' || field.key === 'hospitalised') {
            val = val === true || val === 'true' || val === 1 || val === '1';
          }
          payload[field.key] = val;
        });
        const result = await api.submitPrediction(payload);
        outcomes.push({ row, result, success: true });
      } catch (err) {
        outcomes.push({ row, error: err.message, success: false });
        if (!navigator.onLine) {
          const payload = {};
          FIELDS.forEach(field => {
            payload[field.key] = getRowValue(row, field.key);
          });
          await addDraft({ formData: payload, timestamp: new Date() });
        }
      }
      setProgress({ processed: i + 1, total });
    }

    setResults(outcomes);
    setProcessing(false);
    if (onBatchComplete) onBatchComplete(outcomes);
  };

  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;
  const headers = rows.length > 0 ? Object.keys(rows[0]) : [];

  const getPreview = () => {
    if (rows.length === 0) return {};
    const row = rows[0];
    const preview = {};
    FIELDS.forEach(field => {
      preview[field.key] = getRowValue(row, field.key);
    });
    return preview;
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6">
      <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
        <DocumentArrowUpIcon className="h-5 w-5 text-primary-600" />
        Batch Upload & Predict
      </h3>
      <div className="space-y-4">
        {/* File input */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-full transition font-medium">
            <CloudArrowUpIcon className="h-5 w-5" />
            Choose File
            <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} className="hidden" />
          </label>
          {file && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">{file.name}</span>
              <button onClick={clearFile} className="text-gray-400 hover:text-red-500 transition">
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Column Mapping */}
        {rows.length > 0 && showMapping && (
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 max-h-64 overflow-y-auto">
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <PencilSquareIcon className="h-4 w-4 text-gray-500" />
                Column Mapping
              </h4>
              <button
                onClick={() => setShowMapping(false)}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Hide mapping
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {FIELDS.map(field => {
                const value = columnMapping[field.key] || '';
                return (
                  <div key={field.key} className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 w-24 truncate flex-shrink-0">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-0.5">*</span>}
                    </span>
                    <select
                      value={value}
                      onChange={(e) => setColumnMapping({ ...columnMapping, [field.key]: e.target.value })}
                      className="flex-1 rounded-full border border-gray-300 bg-white px-3 py-1 text-xs focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="">— auto —</option>
                      {headers.map(h => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                );
              })}
            </div>
            <div className="mt-3 p-2 bg-white rounded-lg border border-gray-100">
              <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                <EyeIcon className="h-3 w-3" />
                Preview (first row mapped values)
              </p>
              <div className="flex flex-wrap gap-2 text-xs">
                {Object.entries(getPreview()).map(([key, val]) => (
                  <span key={key} className="bg-gray-100 px-2 py-0.5 rounded">
                    <span className="text-gray-500">{key}:</span>
                    <span className="font-medium ml-1">{String(val)}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Data preview table (scrollable) */}
        {rows.length > 0 && (
          <div className="overflow-x-auto max-h-48 overflow-y-auto">
            <p className="text-sm text-gray-500 mb-2 sticky top-0 bg-white/80 backdrop-blur-sm py-1">
              Preview ({rows.length} rows)
              <span className="ml-2 text-xs text-gray-400">(first 5 shown)</span>
            </p>
            <table className="min-w-full text-xs border-collapse">
              <thead className="bg-gray-50 sticky top-6">
                <tr>
                  {headers.map((key, idx) => (
                    <th key={idx} className="border px-2 py-1 text-left font-medium text-gray-600">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    {headers.map((key, i) => (
                      <td key={i} className="border px-2 py-1 text-gray-700 truncate max-w-[100px]">
                        {String(row[key] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
                {rows.length > 5 && (
                  <tr>
                    <td colSpan={headers.length} className="text-center text-gray-400 py-1">
                      ... and {rows.length - 5} more
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Progress bar */}
        {progress.total > 0 && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Progress</span>
              <span>{progress.processed} / {progress.total}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${(progress.processed / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Results summary */}
        {results.length > 0 && (
          <div className="mt-3 p-3 bg-gray-50 rounded-xl max-h-48 overflow-y-auto">
            <div className="flex items-center gap-4 text-sm mb-2">
              <span className="text-green-600 flex items-center gap-1">
                <CheckCircleIcon className="h-4 w-4" /> {successCount} succeeded
              </span>
              {failCount > 0 && (
                <span className="text-red-600 flex items-center gap-1">
                  <ExclamationCircleIcon className="h-4 w-4" /> {failCount} failed
                </span>
              )}
            </div>
            <div className="space-y-1">
              {results.map((r, idx) => (
                <div
                  key={idx}
                  className={`text-sm flex items-center gap-2 ${r.success ? 'text-green-600' : 'text-red-600'}`}
                >
                  {r.success ? <CheckCircleIcon className="h-4 w-4" /> : <XMarkIcon className="h-4 w-4" />}
                  Row {idx + 1}: {r.success ? 'Submitted' : r.error}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Submit button – ALWAYS VISIBLE */}
        <div className="pt-2 border-t border-gray-200 flex flex-wrap items-center gap-3">
          <button
            onClick={handleBatchSubmit}
            disabled={rows.length === 0 || processing}
            className="px-6 py-2.5 bg-gray-800 hover:bg-gray-900 text-white rounded-full text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            {processing
              ? `Submitting... ${progress.processed}/${progress.total}`
              : `Submit ${rows.length} prediction${rows.length > 1 ? 's' : ''}`}
          </button>
          {results.length > 0 && (
            <button
              onClick={clearFile}
              className="text-sm text-gray-600 hover:text-gray-800 transition"
            >
              Clear all
            </button>
          )}
        </div>
      </div>
    </div>
  );
}