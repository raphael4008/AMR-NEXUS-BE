/**
 * api/endpoints.js
 *
 * Legacy thin wrappers kept for backward-compat.
 * All calls delegate to the authoritative api object in client.js.
 */
import api from './client';

export const predictMDR                = (data)          => api.submitPrediction(data);
export const getSummary                = ()               => api.getSummary();
export const getMDRTrend               = (months = 6)    => api.getMDRTrend(months);
export const getResistanceByPathogen   = (limit = 10)    => api.getByPathogen(limit);
export const getResistanceBySector     = ()               => api.getBySector();
export const getTopCounties            = (limit = 5)     => api.getTopCounties(limit);
export const getPredictionHistory      = (params = {})   => {
  const qs = new URLSearchParams(params).toString();
  return api.getPredictions(params.limit ?? 50, params.skip ?? 0, qs);
};