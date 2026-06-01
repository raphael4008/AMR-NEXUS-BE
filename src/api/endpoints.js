import axios from 'axios';

const apiClient = axios.create({ baseURL: '/api' });

export const fetchSummary = async ({ queryKey }) => {
  const [, role] = queryKey;
  const { data } = await apiClient.get('/summary', { params: { role } });
  return data;
};

export const fetchChoroplethData = async () => {
  const { data } = await apiClient.get('/map/choropleth');
  return data;
};

export const fetchAlerts = async ({ queryKey }) => {
  const [, role] = queryKey;
  const { data } = await apiClient.get('/alerts', { params: { role } });
  return data;
};

export const fetchAlertDetail = async (alertId) => {
  const { data } = await apiClient.get(`/alerts/${alertId}`);
  return data;
};

export const fetchAlertExplanation = async (alertId) => {
  const { data } = await apiClient.get(`/alerts/${alertId}/explanation`);
  return data;
};

export const fetchAlertGuidance = async ({ alertId, role }) => {
  const { data } = await apiClient.get(`/alerts/${alertId}/guidance`, { params: { role } });
  return data;
};

export const fetchTrends = async ({ queryKey }) => {
  const [, pathogen, drug, region, months] = queryKey;
  const { data } = await apiClient.get('/trends', { params: { pathogen, drug, region, months } });
  return data;
};