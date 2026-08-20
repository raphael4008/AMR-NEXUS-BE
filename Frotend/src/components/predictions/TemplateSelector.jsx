import { useState, useEffect } from 'react';
import { DocumentDuplicateIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import api from '../../api/client';

export default function TemplateSelector({ onLoadTemplate, currentFormData }) {
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const data = await api.getTemplates();
      setTemplates(data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setError('Could not load templates.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!templateName || !currentFormData) return;
    try {
      await api.saveTemplate(templateName, currentFormData);
      setTemplateName('');
      setShowSave(false);
      await fetchTemplates();
    } catch (err) {
      console.error('Failed to save template:', err);
      alert('Could not save template.');
    }
  };

  const handleLoad = async (e) => {
    const id = parseInt(e.target.value);
    setSelectedId(e.target.value);
    if (!id) return;
    try {
      const template = templates.find(t => t.id === id);
      if (template) onLoadTemplate(template.form_data);
    } catch (err) {
      console.error('Failed to load template:', err);
    }
  };

  const handleDelete = async () => {
    if (!selectedId) return;
    if (!window.confirm('Delete selected template?')) return;
    try {
      await api.deleteTemplate(parseInt(selectedId));
      setSelectedId('');
      await fetchTemplates();
    } catch (err) {
      console.error('Failed to delete template:', err);
      alert('Could not delete template.');
    }
  };

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 mb-4">
        <div className="flex items-center gap-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          <span className="text-sm">Loading templates...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 mb-4">
        <p className="text-red-500 text-sm">{error}</p>
        <button onClick={fetchTemplates} className="text-primary-600 underline text-sm mt-1">Retry</button>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 mb-4 flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2">
        <DocumentDuplicateIcon className="h-4 w-4 text-gray-400" />
        <select
          onChange={handleLoad}
          value={selectedId}
          className="rounded-full border border-gray-200 bg-white/70 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Load template...</option>
          {templates.map(t => (
            <option key={t.id} value={t.id}>{t.name}</option>
          ))}
        </select>
      </div>

      <button
        onClick={() => setShowSave(!showSave)}
        className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
      >
        <PlusIcon className="h-4 w-4" />
        Save current as template
      </button>

      {showSave && (
        <div className="flex items-center gap-2">
          <input
            value={templateName}
            onChange={e => setTemplateName(e.target.value)}
            placeholder="Template name"
            className="rounded-full border border-gray-200 bg-white/70 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            onClick={handleSave}
            disabled={!templateName || !currentFormData}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary-600 text-white rounded-full text-sm font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PlusIcon className="h-3 w-3" />
            Save
          </button>
          <button
            onClick={() => setShowSave(false)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      )}

      {templates.length > 0 && (
        <button
          onClick={handleDelete}
          className="ml-auto text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          Delete template
        </button>
      )}
    </div>
  );
}