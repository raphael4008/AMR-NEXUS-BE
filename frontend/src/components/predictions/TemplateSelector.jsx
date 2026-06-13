import { useState } from 'react';
import { useTemplateStorage } from '../../hooks/useTemplateStorage';

export default function TemplateSelector({ onLoadTemplate }) {
  const { templates, saveTemplate, deleteTemplate } = useTemplateStorage();
  const [templateName, setTemplateName] = useState('');
  const [showSave, setShowSave] = useState(false);

  const handleSave = (currentFormData) => {
    if (templateName) {
      saveTemplate(templateName, currentFormData);
      setTemplateName('');
      setShowSave(false);
    }
  };

  return (
    <div className="mb-4 flex flex-wrap gap-2 items-center">
      <select onChange={(e) => {
        const id = parseInt(e.target.value);
        const t = templates.find(t => t.id === id);
        if (t) onLoadTemplate(t.formData);
      }} className="rounded-full border px-3 py-1 text-sm">
        <option value="">Load template...</option>
        {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
      </select>
      <button onClick={() => setShowSave(!showSave)} className="text-xs text-primary-600">Save current as template</button>
      {showSave && (
        <div className="flex gap-1">
          <input value={templateName} onChange={e => setTemplateName(e.target.value)} placeholder="Template name" className="rounded-full border px-2 py-1 text-sm" />
          <button onClick={() => handleSave(window.currentFormData)} className="text-xs bg-primary-600 text-white px-2 rounded-full">Save</button>
        </div>
      )}
    </div>
  );
}
