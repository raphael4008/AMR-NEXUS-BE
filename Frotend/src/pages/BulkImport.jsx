import { useState } from 'react';
import * as XLSX from 'xlsx';
import api from '../api/client';
import { toast } from 'react-hot-toast';

export default function BulkImport() {
  const [preview, setPreview] = useState([]);
  const [importing, setImporting] = useState(false);

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet);
      setPreview(rows.slice(0, 10));
    };
    reader.readAsArrayBuffer(file);
  };

  const handleImport = async () => {
    if (preview.length === 0) return;
    setImporting(true);
    let success = 0;
    for (const row of preview) {
      try {
        await api.submitPrediction(row);
        success++;
      } catch (err) {
        console.error(err);
      }
    }
    toast.success(`Imported ${success} of ${preview.length} records`);
    setImporting(false);
    setPreview([]);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Bulk Import Predictions</h1>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6">
        <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFile} className="mb-4" />
        {preview.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm"><thead><tr>{Object.keys(preview[0]).map(k => <th key={k} className="border p-1">{k}</th>)}</tr></thead><tbody>{preview.map((row,i) => <tr key={i}>{Object.values(row).map(v => <td className="border p-1">{String(v).slice(0,20)}</td>)}</tr>)}</tbody></table>
            </div>
            <button onClick={handleImport} disabled={importing} className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-full">Import {preview.length} records</button>
          </>
        )}
      </div>
    </div>
  );
}
