export default function ReportGenerator() {
  const [sending, setSending] = useState(false);
  const handleGenerate = async () => {
    setSending(true);
    await api.generateReport({ email: 'manager@example.com', format: 'pdf' });
    alert('Report queued');
    setSending(false);
  };
  return <Button onClick={handleGenerate} loading={sending}>Email Weekly Report</Button>;
}