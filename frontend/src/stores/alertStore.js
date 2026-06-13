// stores/alertStore.js — Zustand store for alert state
import { create } from 'zustand';

const useAlertStore = create((set) => ({
  alerts: [],
  loading: false,
  error: null,

  setAlerts:  (alerts)  => set({ alerts }),
  setLoading: (loading) => set({ loading }),
  setError:   (error)   => set({ error }),
  clearAlerts: ()       => set({ alerts: [], error: null }),
}));

export default useAlertStore;
