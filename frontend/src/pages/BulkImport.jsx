import { useState } from 'react';
import * as XLSX from 'xlsx';
import api from '../api/client';
import { Toaster, toast } from 'react-hot-toast';

export default function BulkImport() {
  const [allRows, setAllRows]     = useState([]);
  const [preview, setPreview]     = useState([]);
  const [importing, setImporting] = useState(false);
  const [fileName, setFileName]   = useState('');

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data     = new Uint8Array(evt.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheet    = workbook.Sheets[workbook.SheetNames[0]];
      const rows     = XLSX.utils.sheet_to_json(sheet);
      setAllRows(rows);
      setPreview(rows.slice(0, 10));
    };
    reader.readAsArrayBuffer(file);
  };

  const handleImport = async () => {
    if (allRows.length === 0) return;
    setImporting(true);
    try {
      // Send all rows in a single bulk call
      const res = await api.bulkIngest(allRows);
      const ingested = res.data?.ingested ?? res.data?.records?.length ?? allRows.length;
      toast.success(`Successfully imported ${ingested} of ${allRows.length} records`);
      setAllRows([]);
      setPreview([]);
      setFileName('');
    } catch (err) {
      const detail = err.response?.data?.detail ?? err.message ?? 'Unknown error';
      toast.error(`Import failed: ${detail}`);
    } finally {
      setImporting(false);
    }
  };

  const headers = preview.length > 0 ? Object.keys(preview[0]) : [];

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Bulk Import Records</h1>
        {allRows.length > 0 && (
          <span className="text-sm text-gray-500">{allRows.length} rows loaded</span>
        )}
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Excel / CSV File
          </label>
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={handleFile}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
          />
          {fileName && (
            <p className="mt-1 text-xs text-gray-400">📄 {fileName}</p>
          )}
        </div>

        {preview.length > 0 && (
          <>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Preview — first {preview.length} of {allRows.length} rows
              </p>
              <div className="overflow-x-auto rounded-xl border border-gray-200">
                <table className="min-w-full text-xs divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {headers.map(k => (
                        <th key={k} className="px-3 py-2 text-left font-semibold text-gray-600 whitespace-nowrap">
                          {k}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {preview.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {headers.map(k => (
                          <td key={k} className="px-3 py-1.5 text-gray-700 whitespace-nowrap max-w-[120px] overflow-hidden text-ellipsis">
                            {String(row[k] ?? '').slice(0, 25)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <button
              onClick={handleImport}
              disabled={importing}
              className="px-6 py-2 bg-primary-600 text-white rounded-full text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {importing ? (
                <span className="flex items-center gap-2">
                  <span className="inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Importing {allRows.length} records…
                </span>
              ) : (
                `Import All ${allRows.length} Records`
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
