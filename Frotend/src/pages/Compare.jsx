import { useState, useEffect } from 'react';
import { ArrowsRightLeftIcon, DocumentArrowUpIcon } from '@heroicons/react/24/outline';
import api from '../api/client';
import ResultCard from '../components/predictions/ResultCard';
import Select from 'react-select';

const SOURCE_TYPES = [
  { value: 'record', label: 'From Records' },
  { value: 'upload', label: 'Upload File' },
];

function ComparePanel({ side, onData, onClear }) {
  const [sourceType, setSourceType] = useState('record');
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [file, setFile] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        const data = await api.getPredictions(100, 0);
        setRecords(data || []);
      } catch (err) {
        console.error('Failed to load predictions:', err);
        setError('Could not load records.');
      }
    };
    if (sourceType === 'record') fetchRecords();
  }, [sourceType]);

  const handleRecordChange = (option) => {
    setSelectedRecord(option);
    if (option) {
      const record = records.find(r => r.record_id === option.value);
      onData(record);
    } else {
      onData(null);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFile(file);
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target.result;
        let parsed;
        if (file.name.endsWith('.json')) {
          parsed = JSON.parse(text);
        } else if (file.name.endsWith('.csv')) {
          const lines = text.split('\n');
          const headers = lines[0].split(',').map(h => h.trim());
          const rows = lines.slice(1).filter(l => l.trim()).map(line => {
            const values = line.split(',').map(v => v.trim());
            const obj = {};
            headers.forEach((h, i) => obj[h] = values[i]);
            return obj;
          });
          parsed = rows[0] || null;
        } else {
          throw new Error('Unsupported file format. Please upload CSV or JSON.');
        }
        setFileContent(parsed);
        onData(parsed);
        setError(null);
      } catch (err) {
        console.error('File parse error:', err);
        setError('Failed to parse file: ' + err.message);
        onData(null);
      }
    };
    reader.readAsText(file);
  };

  const clearPanel = () => {
    setFile(null);
    setFileContent(null);
    setSelectedRecord(null);
    onData(null);
    setError(null);
    if (sourceType === 'upload') {
      document.getElementById(`file-upload-${side}`).value = '';
    }
    if (sourceType === 'record') {
      setSelectedRecord(null);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-5">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-md font-semibold text-gray-700">
          {side === 'left' ? 'Left' : 'Right'} Source
        </h3>
        <button
          onClick={clearPanel}
          className="text-xs text-red-600 hover:text-red-800 transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        {SOURCE_TYPES.map(type => (
          <button
            key={type.value}
            onClick={() => {
              setSourceType(type.value);
              clearPanel();
            }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              sourceType === type.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {type.label}
          </button>
        ))}
      </div>

      {sourceType === 'record' && (
        <div>
          <Select
            options={records.map(r => ({
              value: r.record_id,
              label: `#${r.record_id?.slice(0, 8)} – ${r.pathogen_code} in ${r.county} (${new Date(r.created_at).toLocaleDateString()})`
            }))}
            value={selectedRecord}
            onChange={handleRecordChange}
            placeholder="Search prediction records..."
            isClearable
            className="text-sm"
            styles={{
              control: (base) => ({
                ...base,
                borderRadius: '9999px',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': { borderColor: '#9ca3af' },
                minHeight: '38px',
              }),
            }}
          />
          {selectedRecord && (
            <p className="text-xs text-gray-500 mt-2">Selected: {selectedRecord.label}</p>
          )}
          {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
        </div>
      )}

      {sourceType === 'upload' && (
        <div>
          <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <DocumentArrowUpIcon className="w-6 h-6 text-gray-400 mb-1" />
              <p className="text-xs text-gray-500">
                {file ? file.name : 'Click to upload CSV or JSON'}
              </p>
            </div>
            <input
              id={`file-upload-${side}`}
              type="file"
              accept=".csv,.json"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
          {fileContent && (
            <div className="mt-2 text-xs text-green-600">
              ✅ File loaded: {file.name}
            </div>
          )}
          {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
        </div>
      )}
    </div>
  );
}

export default function Compare() {
  const [leftData, setLeftData] = useState(null);
  const [rightData, setRightData] = useState(null);

  const handleLeftData = (data) => {
    setLeftData(data);
  };

  const handleRightData = (data) => {
    setRightData(data);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <ArrowsRightLeftIcon className="h-6 w-6 text-primary-600" />
        <h1 className="text-2xl font-bold text-gray-800">Compare Predictions</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <ComparePanel side="left" onData={handleLeftData} />
          {leftData && (
            <div className="mt-4">
              <ResultCard result={leftData} />
            </div>
          )}
        </div>
        <div>
          <ComparePanel side="right" onData={handleRightData} />
          {rightData && (
            <div className="mt-4">
              <ResultCard result={rightData} />
            </div>
          )}
        </div>
      </div>

      {leftData && rightData && (
        <div className="mt-8 p-4 bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50">
          <h3 className="text-md font-semibold mb-3">Diff Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {Object.keys(leftData).filter(k => typeof leftData[k] !== 'object' && typeof leftData[k] !== 'function').map(key => {
              const leftVal = leftData[key];
              const rightVal = rightData[key];
              const isDifferent = leftVal !== rightVal;
              return (
                <div key={key} className={`p-2 rounded ${isDifferent ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'}`}>
                  <span className="font-medium text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                  <div className="flex justify-between mt-1">
                    <span className="text-gray-700">{leftVal ?? '—'}</span>
                    <span className="text-gray-400">vs</span>
                    <span className="text-gray-700">{rightVal ?? '—'}</span>
                  </div>
                  {isDifferent && <span className="text-xs text-yellow-600 block mt-1">⚠️ Different</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}