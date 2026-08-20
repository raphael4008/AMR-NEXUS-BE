import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';
import jsPDF from 'jspdf';
import { toast } from 'react-hot-toast';

export default function ExportSinglePDF({ record }) {
  const exportPDF = () => {
    const doc = new jsPDF();
    const lineHeight = 7;
    let y = 20;

    doc.setFontSize(18);
    doc.text('AMR Prediction Report', 14, y);
    y += lineHeight * 2;

    doc.setFontSize(11);
    const fields = [
      ['Record ID', record.record_id],
      ['Pathogen', record.pathogen_code?.toUpperCase() || 'N/A'],
      ['County', record.county || 'N/A'],
      ['MDR Status', record.mdr_flag ? 'Resistant' : 'Susceptible'],
      ['Probability', `${((record.mdr_probability || 0) * 100).toFixed(1)}%`],
      ['Anomaly', record.anomaly_detected ? 'Yes' : 'No'],
      ['Date', new Date(record.timestamp).toLocaleString()],
      ['SHAP Top Feature', record.shap_top_feature?.replace(/_/g, ' ') || 'N/A'],
      ['SHAP Value', record.shap_value?.toFixed(4) || 'N/A'],
    ];

    fields.forEach(([label, value]) => {
      doc.text(`${label}:`, 14, y);
      doc.text(String(value), 60, y);
      y += lineHeight;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });

    doc.save(`prediction_${record.record_id.slice(0, 8)}.pdf`);
    toast.success('PDF generated');
  };

  return (
    <button onClick={exportPDF} className="p-1 text-gray-400 hover:text-red-500 transition" title="Export PDF">
      <DocumentArrowUpIcon className="h-4 w-4" />
    </button>
  );
}