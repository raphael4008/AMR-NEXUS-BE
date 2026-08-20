import { DocumentArrowDownIcon, DocumentArrowUpIcon, TableCellsIcon } from '@heroicons/react/24/outline';

export default function ExportButtons({ onExcel, onPDF, onCSV }) {
  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={onExcel}
        className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition"
      >
        <TableCellsIcon className="h-4 w-4" /> Excel
      </button>
      <button
        onClick={onPDF}
        className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition"
      >
        <DocumentArrowUpIcon className="h-4 w-4" /> PDF
      </button>
      <button
        onClick={onCSV}
        className="px-4 py-2 border border-gray-300 rounded-full text-sm font-medium flex items-center gap-2 hover:bg-white/60 transition"
      >
        <DocumentArrowDownIcon className="h-4 w-4" /> CSV
      </button>
    </div>
  );
}