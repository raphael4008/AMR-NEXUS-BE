import { useEffect, useState } from 'react';
import {
  SunIcon,
  MoonIcon,
  UserCircleIcon,
  BellIcon,
  DocumentArrowDownIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  DocumentTextIcon,
  ServerIcon,
  CubeIcon,
  TrashIcon,
  CloudArrowUpIcon,
  MapPinIcon,
} from '@heroicons/react/24/outline';
import toast, { Toaster } from 'react-hot-toast';
import { useThemeStore } from '../stores/themeStore';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { useOfflineDrafts } from '../hooks/useOfflineDrafts';
import { counties } from '../utils/constants';

export default function Settings() {
  const { theme, toggleTheme } = useThemeStore();
  const { user, setRoleAndCounty } = useAuth();
  const [backendStatus, setBackendStatus] = useState('checking');
  const [modelInfo, setModelInfo] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [profile, setProfile] = useState({ name: '', email: '', county: '' });
  const [notifications, setNotifications] = useState({
    anomaly: true,
    highMdr: true,
    weeklyReport: false,
  });
  const [retentionDays, setRetentionDays] = useState(365);
  const [auditLogs, setAuditLogs] = useState([]);
  const [editingProfile, setEditingProfile] = useState(false);
  const [loading, setLoading] = useState(false);
  const { drafts, syncDraft } = useOfflineDrafts();

  // Load backend status
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

  // Load profile, notifications, retention from localStorage and API
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await api.getMe();
        setProfile({
          name: data.name || user?.name || '',
          email: data.email || user?.email || '',
          county: data.county || user?.county || '',
        });
      } catch {
        // fallback to AuthContext if API fails
        setProfile({
          name: user?.name || '',
          email: user?.email || '',
          county: user?.county || '',
        });
      }
    };
    loadProfile();

    const savedNotif = localStorage.getItem('notificationPrefs');
    if (savedNotif) setNotifications(JSON.parse(savedNotif));
    const savedRetention = localStorage.getItem('retentionDays');
    if (savedRetention) setRetentionDays(parseInt(savedRetention));

    // In production, fetch audit logs from backend
    // For now, we'll show a placeholder or fetch if endpoint exists
    const fetchAuditLogs = async () => {
      try {
        // If you have an /audit endpoint, use it
        // const logs = await api.getAuditLogs();
        // setAuditLogs(logs);
        // For now, we'll set empty array
        setAuditLogs([]);
      } catch {
        setAuditLogs([]);
      }
    };
    fetchAuditLogs();
  }, []);

  const updateProfile = async () => {
    setLoading(true);
    try {
      // In production, call API to update profile
      // await api.updateMe({ name: profile.name, email: profile.email, county: profile.county });
      // For now, update AuthContext and localStorage
      setRoleAndCounty(user?.role || 'county', profile.county);
      toast.success('Profile updated successfully');
      setEditingProfile(false);
    } catch (err) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const updateNotifications = (key, value) => {
    const newPrefs = { ...notifications, [key]: value };
    setNotifications(newPrefs);
    localStorage.setItem('notificationPrefs', JSON.stringify(newPrefs));
    toast.success('Notification preferences updated');
  };

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      const res = await fetch('http://localhost:8000/export/predictions');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `amr_predictions_${new Date().toISOString().slice(0, 19)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('CSV exported successfully');
    } catch {
      toast.error('Export failed');
    } finally {
      setExporting(false);
    }
  };

  const exportBackup = async () => {
    try {
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
      a.download = `amr_backup_${new Date().toISOString().slice(0, 19)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Backup downloaded');
    } catch {
      toast.error('Backup failed');
    }
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
          toast.success('Restore completed');
        }
      } catch {
        toast.error('Invalid backup file');
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
    if (drafts.length === 0) {
      toast.info('No drafts to sync');
      return;
    }
    try {
      for (const draft of drafts) {
        await syncDraft(draft.id, async (data) => {
          await api.submitPrediction(data.formData);
        });
      }
      toast.success(`${drafts.length} draft(s) synced`);
    } catch {
      toast.error('Sync failed');
    }
  };

  // Component helpers
  const Section = ({ icon, title, children }) => (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 overflow-hidden transition-all hover:shadow-lg">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
        <span className="text-primary-600">{icon}</span>
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
      </div>
      <div className="p-6 space-y-5">{children}</div>
    </div>
  );

  const ActionButton = ({ onClick, icon, label, disabled, variant = 'primary' }) => {
    const base = 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2';
    const variants = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed',
      secondary: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-300',
      danger: 'bg-red-50 text-red-600 hover:bg-red-100 focus:ring-red-500',
    };
    return (
      <button onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]}`}>
        {icon}
        {label}
      </button>
    );
  };

  return (
    <div className="space-y-8">
      <Toaster position="top-right" />
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">v1.0.0</span>
      </div>

      {/* Appearance */}
      <Section icon={theme === 'light' ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />} title="Appearance">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-medium text-gray-800">Theme</h3>
            <p className="text-sm text-gray-500">Switch between light and dark mode</p>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            {theme === 'light' ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />}
          </button>
        </div>
      </Section>

      {/* Profile */}
      <Section icon={<UserCircleIcon className="h-5 w-5" />} title="Profile">
        {editingProfile ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                value={profile.name}
                onChange={e => setProfile({ ...profile, name: e.target.value })}
                className="mt-1 w-full rounded-full border border-gray-300 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                value={profile.email}
                onChange={e => setProfile({ ...profile, email: e.target.value })}
                className="mt-1 w-full rounded-full border border-gray-300 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">County</label>
              <select
                value={profile.county}
                onChange={e => setProfile({ ...profile, county: e.target.value })}
                className="mt-1 w-full rounded-full border border-gray-300 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
              >
                {counties.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-3">
              <ActionButton onClick={updateProfile} icon={<DocumentArrowDownIcon className="h-4 w-4" />} label={loading ? 'Saving...' : 'Save'} disabled={loading} />
              <ActionButton onClick={() => setEditingProfile(false)} variant="secondary" label="Cancel" />
            </div>
          </div>
        ) : (
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium text-gray-800">{profile.name || 'Not set'}</p>
              <p className="text-sm text-gray-500">{profile.email || 'Not set'}</p>
              <p className="text-sm text-gray-500 flex items-center gap-1">
                <MapPinIcon className="h-4 w-4 text-gray-400" />
                {profile.county || 'Not set'}
              </p>
            </div>
            <ActionButton onClick={() => setEditingProfile(true)} variant="secondary" icon={<UserCircleIcon className="h-4 w-4" />} label="Edit" />
          </div>
        )}
      </Section>

      {/* Notifications */}
      <Section icon={<BellIcon className="h-5 w-5" />} title="Notifications">
        <div className="space-y-3">
          <label className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Anomaly alerts</span>
            <input
              type="checkbox"
              checked={notifications.anomaly}
              onChange={e => updateNotifications('anomaly', e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
          </label>
          <label className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">High MDR trend alerts</span>
            <input
              type="checkbox"
              checked={notifications.highMdr}
              onChange={e => updateNotifications('highMdr', e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
          </label>
          <label className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Weekly report email</span>
            <input
              type="checkbox"
              checked={notifications.weeklyReport}
              onChange={e => updateNotifications('weeklyReport', e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
          </label>
        </div>
      </Section>

      {/* Data Management */}
      <Section icon={<DocumentTextIcon className="h-5 w-5" />} title="Data Management">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-gray-800">Export Predictions (CSV)</h3>
              <p className="text-sm text-gray-500">Download all records</p>
            </div>
            <ActionButton onClick={handleExportCSV} icon={<ArrowDownTrayIcon className="h-4 w-4" />} label={exporting ? 'Exporting...' : 'Export'} disabled={exporting} />
          </div>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-gray-800">Backup All Data (JSON)</h3>
              <p className="text-sm text-gray-500">Full export for restore</p>
            </div>
            <ActionButton onClick={exportBackup} variant="secondary" icon={<ArrowDownTrayIcon className="h-4 w-4" />} label="Backup" />
          </div>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-gray-800">Restore from Backup</h3>
              <p className="text-sm text-gray-500">Import JSON backup</p>
            </div>
            <label className="cursor-pointer">
              <input type="file" accept=".json" onChange={importBackup} className="hidden" />
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                <ArrowUpTrayIcon className="h-4 w-4" />
                Restore
              </span>
            </label>
          </div>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-gray-800">Data Retention</h3>
              <p className="text-sm text-gray-500">Keep predictions for</p>
            </div>
            <select
              value={retentionDays}
              onChange={e => {
                setRetentionDays(parseInt(e.target.value));
                localStorage.setItem('retentionDays', e.target.value);
              }}
              className="rounded-full border border-gray-300 px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
            >
              <option value="90">90 days</option>
              <option value="365">1 year</option>
              <option value="1825">5 years</option>
              <option value="0">Forever</option>
            </select>
          </div>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-gray-800">Clear Local Cache</h3>
              <p className="text-sm text-gray-500">Reset preferences</p>
            </div>
            <ActionButton onClick={handleClearCache} variant="danger" icon={<TrashIcon className="h-4 w-4" />} label="Clear Cache" />
          </div>
        </div>
      </Section>

      {/* Offline & Sync */}
      <Section icon={<CloudArrowUpIcon className="h-5 w-5" />} title="Offline & Sync">
        <div className="flex justify-between items-center">
          <div>
            <p className="font-medium text-gray-800">Pending drafts: <span className="text-primary-600">{drafts.length}</span></p>
            <p className="text-sm text-gray-500">Unsynced predictions</p>
          </div>
          <ActionButton onClick={syncAllDrafts} label="Sync now" icon={<CloudArrowUpIcon className="h-4 w-4" />} disabled={drafts.length === 0} />
        </div>
      </Section>

      {/* System Status */}
      <Section icon={<ServerIcon className="h-5 w-5" />} title="System Status">
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-700">Backend API</span>
          <div className="flex items-center gap-2">
            <span className={`inline-block h-2.5 w-2.5 rounded-full ${backendStatus === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm font-medium capitalize">{backendStatus}</span>
          </div>
        </div>
        {modelInfo && (
          <div className="flex justify-between items-center">
            <span className="font-medium text-gray-700">ML Model</span>
            <span className="text-sm bg-gray-100 px-3 py-1 rounded-full">{modelInfo.service} {modelInfo.version}</span>
          </div>
        )}
      </Section>

      {/* Audit Log */}
      <Section icon={<ClockIcon className="h-5 w-5" />} title="Audit Log">
        <div className="max-h-48 overflow-y-auto space-y-1">
          {auditLogs.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
          ) : (
            auditLogs.map(log => (
              <div key={log.id} className="text-sm border-b py-2 flex justify-between">
                <span>{log.action}</span>
                <span className="text-gray-400 text-xs">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
            ))
          )}
        </div>
      </Section>

      {/* About */}
      <Section icon={<CubeIcon className="h-5 w-5" />} title="About">
        <p className="text-sm text-gray-700">
          <strong>AMR‑Nexus One Health Platform</strong><br />
          Version 1.0.0 | React + Vite | FastAPI + ML
        </p>
        <p className="text-xs text-gray-400">© {new Date().getFullYear()} AMR‑Nexus. All rights reserved.</p>
      </Section>
    </div>
  );
}