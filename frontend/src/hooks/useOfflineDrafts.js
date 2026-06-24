import { useState, useEffect } from 'react';
import { initDB, saveDraft, getDrafts, deleteDraft, markSynced } from '../utils/offlineStorage';

export function useOfflineDrafts() {
  const [drafts, setDrafts] = useState([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    initDB().then(() => {
      loadDrafts();
      setIsReady(true);
    });
  }, []);

  const loadDrafts = async () => {
    const all = await getDrafts();
    setDrafts(all);
  };

  const addDraft = async (data) => {
    await saveDraft(data);
    await loadDrafts();
  };

  const removeDraft = async (id) => {
    await deleteDraft(id);
    await loadDrafts();
  };

  const syncDraft = async (id, submitFn) => {
    const draft = drafts.find(d => d.id === id);
    if (!draft) return;
    try {
      await submitFn(draft.formData);
      await markSynced(id);
      await loadDrafts();
    } catch (err) {
      console.error('Sync failed', err);
    }
  };

  return { drafts, isReady, addDraft, removeDraft, syncDraft };
}
