import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { toast } from 'react-hot-toast';

export default function ExportAnalyticsButton({ targetId, fileName }) {
  const handleExport = async () => {
    const element = document.getElementById(targetId);
    if (!element) return;
    toast.loading('Generating PDF...', { id: 'pdf' });
    try {
      const canvas = await html2canvas(element, { scale: 2, backgroundColor: '#f9fafb' });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
      pdf.save(`${fileName || 'analytics'}_${new Date().toISOString().slice(0,19)}.pdf`);
      toast.success('PDF exported', { id: 'pdf' });
    } catch (err) {
      toast.error('Export failed', { id: 'pdf' });
    }
  };
  return (
    <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-full text-sm">
      <DocumentArrowDownIcon className="h-4 w-4" /> Export PDF
    </button>
  );
}