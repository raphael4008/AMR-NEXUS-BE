import { useState } from 'react';
import { DocumentDuplicateIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useTemplateStorage } from '../../hooks/useTemplateStorage';

export default function TemplateSelector({ onLoadTemplate, currentFormData }) {
  const { templates, saveTemplate, deleteTemplate } = useTemplateStorage();
  const [templateName, setTemplateName] = useState('');
  const [showSave, setShowSave] = useState(false);

  const handleSave = () => {
    if (templateName && currentFormData) {
      saveTemplate(templateName, currentFormData);
      setTemplateName('');
      setShowSave(false);
    }
  };

  const handleLoad = (e) => {
    const id = parseInt(e.target.value);
    const t = templates.find(t => t.id === id);
    if (t) onLoadTemplate(t.formData);
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-md border border-white/50 p-4 mb-4 flex flex-wrap items-center gap-3">
      {/* Template dropdown */}
      <div className="flex items-center gap-2">
        <DocumentDuplicateIcon className="h-4 w-4 text-gray-400" />
        <select
          onChange={handleLoad}
          className="rounded-full border border-gray-200 bg-white/70 px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Load template...</option>
          {templates.map(t => (
            <option key={t.id} value={t.id}>{t.name}</option>
          ))}
        </select>
      </div>

      {/* Save template toggle */}
      <button
        onClick={() => setShowSave(!showSave)}
        className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
      >
        <PlusIcon className="h-4 w-4" />
        Save current as template
      </button>

      {/* Save input (conditional) */}
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

      {/* Delete template (if any selected) */}
      {templates.length > 0 && (
        <button
          onClick={() => {
            if (window.confirm('Delete selected template?')) {
              const select = document.querySelector('select');
              if (select && select.value) {
                deleteTemplate(parseInt(select.value));
                select.value = '';
              }
            }
          }}
          className="ml-auto text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          Delete template
        </button>
      )}
    </div>
  );
}