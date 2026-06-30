import api from './client';

export const predictMDR = async (data) => {
  const response = await api.post('/predict', data);
  return response.data;
};

export const getSummary = async () => {
  const response = await api.get('/analytics/summary');
  return response.data;
};

export const getMDRTrend = async (months = 6) => {
  const response = await api.get(`/analytics/mdr_trend?months=${months}`);
  return response.data;
};

export const getResistanceByPathogen = async (limit = 10) => {
  const response = await api.get(`/analytics/by_pathogen?limit=${limit}`);
  return response.data;
};

export const getResistanceBySector = async () => {
  const response = await api.get('/analytics/by_sector');
  return response.data;
};

export const getTopCounties = async (limit = 5) => {
  const response = await api.get(`/analytics/top_counties?limit=${limit}`);
  return response.data;
};

// Add this if you implement prediction history endpoint
export const getPredictionHistory = async (params) => {
  const response = await api.get('/predictions', { params });
  return response.data;
};