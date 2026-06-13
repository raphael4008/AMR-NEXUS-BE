import { useEffect, useState } from 'react';
import {
  SunIcon, MoonIcon, UserCircleIcon, EnvelopeIcon, KeyIcon, BellIcon,
  ArrowDownTrayIcon, ArrowUpTrayIcon, ClockIcon, DocumentTextIcon,
  ServerIcon, CubeIcon, TrashIcon, ShieldCheckIcon, LanguageIcon,
  CalendarDaysIcon, CloudArrowUpIcon, EyeIcon
} from '@heroicons/react/24/outline';
import { useThemeStore } from '../stores/themeStore';
import api from '../api/client';
import { useOfflineDrafts } from '../hooks/useOfflineDrafts';

export default function Settings() {
  const { theme, toggleTheme } = useThemeStore();
  const [backendStatus, setBackendStatus] = useState('checking');
  const [modelInfo, setModelInfo] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [offlineDrafts, setOfflineDrafts] = useState([]);
  const [profile, setProfile] = useState({ name: '', email: '' });
  const [apiKeys, setApiKeys] = useState([]);
  const [notifications, setNotifications] = useState({
    anomaly: true,
    highMdr: true,
    weeklyReport: false,
  });
  const [retentionDays, setRetentionDays] = useState(365);
  const [auditLogs, setAuditLogs] = useState([]);
  const [editingProfile, setEditingProfile] = useState(false);
  const [newApiKeyName, setNewApiKeyName] = useState('');
  const [showApiKey, setShowApiKey] = useState(null);
  const { drafts, syncDraft } = useOfflineDrafts();

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await api.health();
        setBackendStatus('online');
        setModelInfo({ service: health.service, version: health.version || 'v1.0' });
      } catch {
        setBackendStatus('offline');
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    api.getMe().then(data => {
      if (data) setProfile({ name: data.name ?? '', email: data.email ?? '' });
    }).catch(() => {});
    const savedNotif = localStorage.getItem('notificationPrefs');
    if (savedNotif) {
      try { setNotifications(JSON.parse(savedNotif)); } catch {}
    }
    const savedRetention = localStorage.getItem('retentionDays');
    if (savedRetention) setRetentionDays(parseInt(savedRetention));
    setApiKeys([{ id: 1, name: 'Default Key', key: 'amr_live_abc123', createdAt: '2025-01-01' }]);
    setAuditLogs([
      { id: 1, user: 'john.doe@amrnexus.org', action: 'Exported predictions', timestamp: new Date().toISOString() },
      { id: 2, user: 'john.doe@amrnexus.org', action: 'Changed notification preferences', timestamp: new Date().toISOString() },
    ]);
  }, []);

  const updateProfile = async () => {
    alert('Profile updated (mock)');
    setEditingProfile(false);
  };

  const updateNotifications = (key, value) => {
    const newPrefs = { ...notifications, [key]: value };
    setNotifications(newPrefs);
    localStorage.setItem('notificationPrefs', JSON.stringify(newPrefs));
  };

  const generateApiKey = () => {
    if (!newApiKeyName) return;
    const newKey = `amr_${Math.random().toString(36).substring(2, 15)}`;
    setApiKeys([...apiKeys, { id: Date.now(), name: newApiKeyName, key: newKey, createdAt: new Date().toISOString().split('T')[0] }]);
    setNewApiKeyName('');
  };
  const revokeApiKey = (id) => setApiKeys(apiKeys.filter(k => k.id !== id));

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      await api.exportRecordsCSV();
    } catch {
      alert('Export failed');
    } finally {
      setExporting(false);
    }
  };

  const exportBackup = async () => {
    const predictions = await api.getPredictions(10000, 0);
    const backup = {
      predictions,
      settings: { notifications, retentionDays },
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `amr_backup_${new Date().toISOString().slice(0,19)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importBackup = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.settings) {
          setNotifications(data.settings.notifications);
          localStorage.setItem('notificationPrefs', JSON.stringify(data.settings.notifications));
          setRetentionDays(data.settings.retentionDays);
          localStorage.setItem('retentionDays', data.settings.retentionDays);
        }
        alert('Restore completed (predictions not imported – use bulk import)');
      } catch {
        alert('Invalid backup file');
      }
    };
    reader.readAsText(file);
  };

  const handleClearCache = () => {
    if (window.confirm('Clear all local storage and reload?')) {
      localStorage.clear();
      window.location.reload();
    }
  };

  const syncAllDrafts = async () => {
    for (const draft of drafts) {
      await syncDraft(draft.id, async (data) => {
        await api.submitPrediction(data.formData);
      });
    }
    alert('Drafts synced');
  };

  const Section = ({ icon, title, children }) => (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 overflow-hidden">
      <div className="p-5 border-b border-gray-100 flex items-center gap-2">
        <span className="text-gray-700">{icon}</span>
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
      </div>
      <div className="p-5 space-y-4 text-gray-700">{children}</div>
    </div>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      <Section icon={theme === 'light' ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />} title="Appearance">
        <div className="flex justify-between items-center">
          <div><h3 className="font-medium">Theme</h3><p className="text-sm text-gray-500">Switch between light and dark mode</p></div>
          <button onClick={toggleTheme} className="p-2 rounded-full bg-gray-100">
            {theme === 'light' ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />}
          </button>
        </div>
      </Section>

      <Section icon={<UserCircleIcon className="h-5 w-5" />} title="Profile">
        {editingProfile ? (
          <div className="space-y-3">
            <input value={profile.name} onChange={e => setProfile({...profile, name: e.target.value})} className="w-full rounded-full border p-2" placeholder="Name" />
            <input value={profile.email} onChange={e => setProfile({...profile, email: e.target.value})} className="w-full rounded-full border p-2" placeholder="Email" />
            <div className="flex gap-2"><button onClick={updateProfile} className="px-4 py-1 bg-primary-600 text-white rounded-full">Save</button><button onClick={() => setEditingProfile(false)} className="px-4 py-1 border rounded-full">Cancel</button></div>
          </div>
        ) : (
          <div className="flex justify-between items-center"><div><p className="font-medium">{profile.name}</p><p className="text-sm text-gray-500">{profile.email}</p></div><button onClick={() => setEditingProfile(true)} className="text-primary-600">Edit</button></div>
        )}
      </Section>

      <Section icon={<BellIcon className="h-5 w-5" />} title="Notifications">
        <div className="space-y-2">
          <label className="flex justify-between items-center"><span>Anomaly alerts</span><input type="checkbox" checked={notifications.anomaly} onChange={e => updateNotifications('anomaly', e.target.checked)} className="rounded" /></label>
          <label className="flex justify-between items-center"><span>High MDR trend alerts</span><input type="checkbox" checked={notifications.highMdr} onChange={e => updateNotifications('highMdr', e.target.checked)} /></label>
          <label className="flex justify-between items-center"><span>Weekly report email</span><input type="checkbox" checked={notifications.weeklyReport} onChange={e => updateNotifications('weeklyReport', e.target.checked)} /></label>
        </div>
      </Section>

      <Section icon={<KeyIcon className="h-5 w-5" />} title="API Keys">
        <div className="space-y-3">
          {apiKeys.map(k => (
            <div key={k.id} className="flex justify-between items-center border-b pb-2">
              <div><p className="font-mono text-sm">{k.name}</p><p className="text-xs text-gray-500">Created {k.createdAt}</p></div>
              <div className="flex gap-2"><button onClick={() => setShowApiKey(showApiKey === k.id ? null : k.id)}><EyeIcon className="h-4 w-4" /></button><button onClick={() => revokeApiKey(k.id)}><TrashIcon className="h-4 w-4 text-red-500" /></button></div>
              {showApiKey === k.id && <p className="text-xs font-mono bg-gray-100 p-1 rounded">{k.key}</p>}
            </div>
          ))}
          <div className="flex gap-2 mt-2"><input value={newApiKeyName} onChange={e => setNewApiKeyName(e.target.value)} placeholder="Key name" className="flex-1 rounded-full border p-1 text-sm" /><button onClick={generateApiKey} className="px-3 py-1 bg-primary-600 text-white rounded-full text-sm">Generate</button></div>
        </div>
      </Section>

      <Section icon={<DocumentTextIcon className="h-5 w-5" />} title="Data Management">
        <div className="space-y-4">
          <div className="flex justify-between items-center"><div><h3 className="font-medium">Export Predictions (CSV)</h3><p className="text-sm text-gray-500">Download all records</p></div><button onClick={handleExportCSV} disabled={exporting} className="px-4 py-1 bg-primary-600 text-white rounded-full">📥 Export</button></div>
          <div className="flex justify-between items-center"><div><h3 className="font-medium">Backup All Data (JSON)</h3><p className="text-sm text-gray-500">Full export for restore</p></div><button onClick={exportBackup} className="px-4 py-1 border rounded-full">📦 Backup</button></div>
          <div className="flex justify-between items-center"><div><h3 className="font-medium">Restore from Backup</h3><p className="text-sm text-gray-500">Import JSON backup</p></div><input type="file" accept=".json" onChange={importBackup} className="text-sm" /></div>
          <div className="flex justify-between items-center"><div><h3 className="font-medium">Data Retention (days)</h3><p className="text-sm text-gray-500">Keep predictions for</p></div><select value={retentionDays} onChange={e => { setRetentionDays(parseInt(e.target.value)); localStorage.setItem('retentionDays', e.target.value); }} className="rounded-full border p-1"><option value="90">90 days</option><option value="365">1 year</option><option value="1825">5 years</option><option value="0">Forever</option></select></div>
          <div className="flex justify-between items-center"><div><h3 className="font-medium">Clear Local Cache</h3><p className="text-sm text-gray-500">Reset preferences</p></div><button onClick={handleClearCache} className="px-4 py-1 bg-red-100 text-red-600 rounded-full">Clear Cache</button></div>
        </div>
      </Section>

      <Section icon={<CloudArrowUpIcon className="h-5 w-5" />} title="Offline & Sync">
        <div className="flex justify-between items-center"><div><p className="font-medium">Pending drafts: {drafts.length}</p><p className="text-sm text-gray-500">Unsynced predictions</p></div><button onClick={syncAllDrafts} disabled={drafts.length === 0} className="px-4 py-1 bg-primary-600 text-white rounded-full">Sync now</button></div>
      </Section>

      <Section icon={<ServerIcon className="h-5 w-5" />} title="System Status">
        <div className="flex justify-between items-center"><span>Backend API</span><div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${backendStatus === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span><span className="capitalize">{backendStatus}</span></div></div>
        {modelInfo && <div className="flex justify-between items-center mt-2"><span>ML Model</span><span className="text-sm bg-gray-100 px-2 py-1 rounded-full">{modelInfo.service} {modelInfo.version}</span></div>}
      </Section>

      <Section icon={<ClockIcon className="h-5 w-5" />} title="Audit Log">
        <div className="max-h-48 overflow-y-auto">{auditLogs.map(log => (<div key={log.id} className="text-sm border-b py-1 flex justify-between"><span>{log.action}</span><span className="text-gray-500">{new Date(log.timestamp).toLocaleString()}</span></div>))}</div>
      </Section>

      <Section icon={<CubeIcon className="h-5 w-5" />} title="About">
        <p className="text-sm"><strong>AMR‑Nexus One Health Platform</strong><br />Version 1.0.0 | React + Vite | FastAPI + ML</p>
        <p className="text-xs text-gray-400 mt-2">© {new Date().getFullYear()} AMR‑Nexus. All rights reserved.</p>
      </Section>
    </div>
  );
}
