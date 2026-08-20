import { useState, useEffect, useCallback } from 'react';
import { initDB, saveDraft, getDrafts, deleteDraft, markSynced, clearAllDrafts } from '../utils/offlineStorage';

export function useOfflineDrafts() {
  const [drafts, setDrafts] = useState([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    initDB().then(() => {
      loadDrafts();
      setIsReady(true);
    });
  }, []);

  const loadDrafts = useCallback(async () => {
    const all = await getDrafts();
    setDrafts(all);
  }, []);

  const addDraft = useCallback(async (data) => {
    await saveDraft(data);
    await loadDrafts();
  }, [loadDrafts]);

  const removeDraft = useCallback(async (id) => {
    await deleteDraft(id);
    await loadDrafts();
  }, [loadDrafts]);

  const clearDrafts = useCallback(async () => {
    await clearAllDrafts();
    await loadDrafts();
  }, [loadDrafts]);

  const syncDraft = useCallback(async (id, submitFn) => {
    const draft = drafts.find(d => d.id === id);
    if (!draft) throw new Error('Draft not found');
    try {
      await submitFn(draft.formData);
      await markSynced(id);
      await loadDrafts();
      return true;
    } catch (err) {
      console.error('Sync failed', err);
      throw err;
    }
  }, [drafts, loadDrafts]);

  return { drafts, isReady, addDraft, removeDraft, clearDrafts, syncDraft };
}