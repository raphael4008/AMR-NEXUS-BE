import { useState } from 'react';
import * as XLSX from 'xlsx';
import api from '../api/client';
import { toast } from 'react-hot-toast';
import { Toaster } from 'react-hot-toast';

/**
 * Maps a raw XLSX/CSV row to an AMRRecordCreate-compatible object.
 * Accepts common column name variations from lab Excel exports.
 */
function mapRowToSchema(row) {
  const get = (...keys) => {
    for (const k of keys) {
      const val = row[k] ?? row[k?.toLowerCase()] ?? row[k?.toUpperCase()];
      if (val !== undefined && val !== null && val !== '') return String(val).trim();
    }
    return undefined;
  };

  const sirRaw = get('sir_result', 'SIR Result', 'SIR', 'Result', 'Interpretation');
  const sirMap = { resistant: 'R', intermediate: 'I', susceptible: 'S', r: 'R', i: 'I', s: 'S' };
  const sir_result = sirMap[sirRaw?.toLowerCase()] ?? sirRaw;

  const sectorRaw = get('sector', 'Sector', 'SECTOR');
  const sectorMap = {
    human: 'HUMAN', human_health: 'HUMAN', hospital: 'HUMAN',
    animal: 'ANIMAL', veterinary: 'ANIMAL', livestock: 'ANIMAL',
    environment: 'ENVIRONMENT', food: 'FOOD_CHAIN', food_chain: 'FOOD_CHAIN',
  };
  const sector = sectorMap[sectorRaw?.toLowerCase()?.replace(/\s/g, '_')] ?? sectorRaw;

  return {
    pathogen_name:          get('pathogen_name', 'Pathogen', 'pathogen', 'Organism'),
    antibiotic_name:        get('antibiotic_name', 'Antibiotic', 'antibiotic', 'Drug', 'Antimicrobial'),
    sir_result,
    sector,
    county:                 get('county', 'County', 'COUNTY'),
    sub_county:             get('sub_county', 'Sub County', 'SubCounty', 'sub_county'),
    sample_collection_date: get('sample_collection_date', 'Collection Date', 'Date', 'Sample Date'),
    sample_id:              get('sample_id', 'Sample ID', 'SampleID', 'ID'),
    facility_name:          get('facility_name', 'Facility', 'Facility Name', 'Hospital'),
    antibiotic_class:       get('antibiotic_class', 'Antibiotic Class', 'Drug Class'),
    mic_value:              parseFloat(get('mic_value', 'MIC', 'MIC Value')) || undefined,
    specimen_type:          get('specimen_type', 'Specimen', 'Specimen Type', 'Sample Type'),
    patient_age_group:      get('patient_age_group', 'Age Group', 'Patient Age Group'),
    patient_sex:            get('patient_sex', 'Sex', 'Patient Sex', 'Gender'),
    latitude:               parseFloat(get('latitude', 'Latitude', 'Lat')) || undefined,
    longitude:              parseFloat(get('longitude', 'Longitude', 'Long', 'Lon')) || undefined,
  };
}

export default function BulkImport() {
  const [rawRows, setRawRows]     = useState([]);
  const [mapped, setMapped]       = useState([]);
  const [importing, setImporting] = useState(false);
  const [result, setResult]       = useState(null);

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet);
      setRawRows(rows);
      setMapped(rows.map(mapRowToSchema));
      setResult(null);
    };
    reader.readAsArrayBuffer(file);
  };

  const handleImport = async () => {
    if (!mapped.length) return;
    setImporting(true);
    setResult(null);
    try {
      const res = await api.bulkIngest(mapped);
      setResult(res);
      toast.success(`Imported ${res.processed_records} records. Analysis ${res.task_queued ? 'queued' : 'pending'}.`);
      setRawRows([]);
      setMapped([]);
    } catch (err) {
      toast.error('Import failed: ' + err.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />
      <h1 className="text-2xl font-bold">Bulk Import AMR Records</h1>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-md border">
        <p className="text-sm text-gray-500 mb-4">
          Upload an <strong>.xlsx</strong>, <strong>.xls</strong> or <strong>.csv</strong> file.
          Required columns: <code>pathogen_name</code>, <code>antibiotic_name</code>, <code>sir_result</code>,
          <code>sector</code>, <code>county</code>, <code>sample_collection_date</code>.
        </p>
        <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFile} className="mb-4" />

        {mapped.length > 0 && (
          <>
            <p className="text-sm font-medium mb-2">{mapped.length} rows detected — preview (first 5):</p>
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full text-xs border rounded">
                <thead className="bg-gray-50">
                  <tr>
                    {['pathogen_name','antibiotic_name','sir_result','sector','county','sample_collection_date'].map(k => (
                      <th key={k} className="border p-1 text-left">{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mapped.slice(0, 5).map((row, i) => (
                    <tr key={i} className="odd:bg-white even:bg-gray-50">
                      {['pathogen_name','antibiotic_name','sir_result','sector','county','sample_collection_date'].map(k => (
                        <td key={k} className="border p-1">{String(row[k] ?? '—').slice(0, 25)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              onClick={handleImport}
              disabled={importing}
              className="px-6 py-2 bg-primary-600 text-white rounded-full font-medium disabled:opacity-50"
            >
              {importing ? 'Importing...' : `Import ${mapped.length} records`}
            </button>
          </>
        )}

        {result && (
          <div className="mt-4 p-4 bg-green-50 rounded-xl border border-green-200">
            <p className="font-medium text-green-800">Import Complete</p>
            <p className="text-sm text-green-600">{result.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
