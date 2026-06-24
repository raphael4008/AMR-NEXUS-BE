import { useState, useEffect } from 'react';

const STORAGE_KEY = 'prediction_templates';

export function useTemplateStorage() {
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) setTemplates(JSON.parse(stored));
  }, []);

  const saveTemplate = (name, formData) => {
    const newTemplate = { id: Date.now(), name, formData };
    const updated = [...templates, newTemplate];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setTemplates(updated);
  };

  const deleteTemplate = (id) => {
    const updated = templates.filter(t => t.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setTemplates(updated);
  };

  return { templates, saveTemplate, deleteTemplate };
}
