import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

export default function ExportSinglePDF({ record }) {
  const exportPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(18);
    doc.text('AMR Prediction Report', 14, 22);
    doc.setFontSize(12);
    doc.text(`Record ID: ${record.record_id}`, 14, 32);
    doc.text(`Pathogen: ${record.pathogen_code?.toUpperCase()}`, 14, 42);
    doc.text(`County: ${record.county}`, 14, 52);
    doc.text(`MDR Status: ${record.mdr_flag ? 'Resistant' : 'Susceptible'}`, 14, 62);
    doc.text(`Probability: ${((record.mdr_probability||0)*100).toFixed(1)}%`, 14, 72);
    doc.text(`Anomaly: ${record.anomaly_detected ? 'Yes' : 'No'}`, 14, 82);
    doc.text(`Date: ${new Date(record.timestamp).toLocaleString()}`, 14, 92);
    doc.save(`prediction_${record.record_id.slice(0,8)}.pdf`);
  };

  return (
    <button onClick={exportPDF} className="p-1 text-gray-400 hover:text-red-500 transition" title="Export PDF">
      <DocumentArrowUpIcon className="h-4 w-4" />
    </button>
  );
}