// stores/predictionStore.js
import { create } from 'zustand';
import api from '../api/client';

const usePredictionStore = create((set) => ({
  currentResult: null,
  isLoading: false,
  submitPrediction: async (data) => {
    set({ isLoading: true });
    try {
      const result = await api.submitPrediction(data);
      set({ currentResult: result, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
}));

export default usePredictionStore;