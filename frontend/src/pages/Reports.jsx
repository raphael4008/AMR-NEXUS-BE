import { useState, useEffect, useCallback } from 'react';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import api from '../api/client';
import ReportFilters from '../components/reports/ReportFilters';
import ReportPreview from '../components/reports/ReportPreview';
import ExportButtons from '../components/reports/ExportButtons';
import ScheduleModal from '../components/reports/ScheduleModal';

export default function Reports() {
  const [reportType, setReportType] = useState('mdr_summary');
  const [dateRange, setDateRange] = useState('last30');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  const getDateParams = useCallback(() => {
    const now = new Date();
    let start = null, end = now;
    if (dateRange === 'last7') start = new Date(now.setDate(now.getDate() - 7));
    else if (dateRange === 'last30') start = new Date(now.setDate(now.getDate() - 30));
    else if (dateRange === 'last90') start = new Date(now.setDate(now.getDate() - 90));
    else if (dateRange === 'custom' && startDate && endDate) {
      start = new Date(startDate);
      end = new Date(endDate);
    }
    return { start, end };
  }, [dateRange, startDate, endDate]);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const { start, end } = getDateParams();
      const query = new URLSearchParams();
      if (start) query.append('start_date', start.toISOString().split('T')[0]);
      if (end) query.append('end_date', end.toISOString().split('T')[0]);
      const qs = query.toString();

      let data = {};
      switch (reportType) {
        case 'mdr_summary':
          data = await api.getSummary(qs);
          break;
        case 'anomaly_report':
          const predictions = await api.getPredictions(1000, 0, qs);
          const anomalies = predictions.filter(p => p.anomaly_detected);
          data = {
            total_predictions: predictions.length,
            anomaly_count: anomalies.length,
            anomaly_rate: anomalies.length / predictions.length * 100 || 0,
            recent_anomalies: anomalies.slice(0, 10),
          };
          break;
        case 'sector_comparison':
          data = { sectors: await api.getBySector(qs) };
          break;
        case 'county_ranking':
          data = { counties: await api.getTopCounties(10, qs) };
          break;
        case 'pathogen_wise':
          data = { pathogens: await api.getByPathogen(20, qs) };
          break;
        case 'trend': {
          // getMDRTrend now returns a plain normalised array [{month, rate, ...}]
          const trendArr = await api.getMDRTrend(12, qs);
          data = { trend: Array.isArray(trendArr) ? trendArr : [] };
          break;
        }
        default:
          data = await api.getSummary(qs);
      }
      setReportData(data);
    } catch (err) {
      console.error(err);
      setReportData({ error: 'Failed to load report. Check backend connectivity.' });
    } finally {
      setLoading(false);
    }
  }, [reportType, getDateParams]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const exportExcel = () => {
    if (!reportData) return alert('No data to export');
    let sheetData = [];
    if (reportType === 'mdr_summary') sheetData = [['Metric', 'Value'], ['Total Records', reportData.total_records || 0], ['MDR Rate (%)', reportData.mdr_rate || 0], ['Anomalies', reportData.anomaly_count || 0], ['Active Counties', reportData.active_counties || 0]];
    else if (reportType === 'sector_comparison' && reportData.sectors) sheetData = [['Sector', 'MDR (%)'], ...reportData.sectors.map(s => [s.name, s.value])];
    else if (reportType === 'county_ranking' && reportData.counties) sheetData = [['County', 'MDR (%)'], ...reportData.counties.map(c => [c.county, c.rate])];
    else if (reportType === 'pathogen_wise' && reportData.pathogens) sheetData = [['Pathogen', 'Resistance (%)'], ...reportData.pathogens.map(p => [p.name, p.resistance])];
    else if (reportType === 'trend' && reportData.trend) sheetData = [['Month', 'MDR Rate (%)'], ...reportData.trend.map(t => [t.month, t.rate])];
    else return alert('Unsupported report type for Excel export');
    const ws = XLSX.utils.aoa_to_sheet(sheetData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Report');
    XLSX.writeFile(wb, `amr_report_${reportType}_${new Date().toISOString().slice(0,19)}.xlsx`);
  };

  const exportCSV = () => {
    if (!reportData) return alert('No data to export');
    let csvRows = [];
    if (reportType === 'mdr_summary') csvRows = [['Metric','Value'],[`Total Records,${reportData.total_records || 0}`],[`MDR Rate (%),${reportData.mdr_rate || 0}`],[`Anomalies,${reportData.anomaly_count || 0}`],[`Active Counties,${reportData.active_counties || 0}`]];
    else if (reportType === 'sector_comparison' && reportData.sectors) csvRows = [['Sector','MDR (%)'], ...reportData.sectors.map(s => [s.name, s.value])];
    else if (reportType === 'county_ranking' && reportData.counties) csvRows = [['County','MDR (%)'], ...reportData.counties.map(c => [c.county, c.rate])];
    else if (reportType === 'pathogen_wise' && reportData.pathogens) csvRows = [['Pathogen','Resistance (%)'], ...reportData.pathogens.map(p => [p.name, p.resistance])];
    else if (reportType === 'trend' && reportData.trend) csvRows = [['Month','MDR Rate (%)'], ...reportData.trend.map(t => [t.month, t.rate])];
    else return alert('CSV export not supported for this report type');
    const csvContent = csvRows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `amr_report_${reportType}_${new Date().toISOString().slice(0,19)}.csv`);
  };

  const exportPDF = async () => {
    setExportingPDF(true);
    const element = document.getElementById('report-preview-content');
    if (!element) return;
    try {
      const canvas = await html2canvas(element, { scale: 2, backgroundColor: '#ffffff' });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
      pdf.save(`amr_report_${reportType}_${new Date().toISOString().slice(0,19)}.pdf`);
    } catch (err) {
      console.error(err);
      alert('PDF generation failed');
    }
    setExportingPDF(false);
  };

  const scheduleReport = async (email, schedule) => {
    setScheduling(true);
    try {
      await api.emailReport({ email, format: 'pdf', type: reportType, schedule });
      alert(`Report scheduled ${schedule}ly to ${email}.`);
      setShowScheduleModal(false);
    } catch (err) {
      alert('Failed to schedule. Ensure backend endpoint exists.');
    } finally {
      setScheduling(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Reports & Intelligence</h1>
        <ExportButtons onExcel={exportExcel} onPDF={exportPDF} onCSV={exportCSV} />
      </div>

      <ReportFilters
        reportType={reportType}
        setReportType={setReportType}
        dateRange={dateRange}
        setDateRange={setDateRange}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        onRefresh={fetchReport}
      />

      <div id="report-preview-content">
        <ReportPreview reportType={reportType} data={reportData} loading={loading} />
      </div>

      <div className="flex justify-end">
        <button onClick={() => setShowScheduleModal(true)} className="flex items-center gap-2 px-5 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-full text-sm font-medium">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" /></svg>
          Schedule Email Report
        </button>
      </div>

      <ScheduleModal isOpen={showScheduleModal} onClose={() => setShowScheduleModal(false)} onSchedule={scheduleReport} scheduling={scheduling} />
    </div>
  );
}