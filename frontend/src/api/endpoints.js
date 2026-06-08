import axios from 'axios';

// Base API Configuration
const apiClient = axios.create({
  baseURL: 'http://localhost:8080/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

/**
 * Request Interceptor: 
 * Ensures every request automatically attaches the Bearer token 
 * from localStorage if the user is authenticated.
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('amr_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// ── Intelligence Endpoints ──────────────────────────────────────────

export const fetchSummary = async ({ queryKey }) => {
  const [, role] = queryKey;
  try {
    const { data } = await apiClient.get('/intelligence/dashboard/summary', { params: { role } });
    return {
      totalIsolates: data.total_isolates_scanned || 0,
      activeAnomalies: data.active_hotspots_detected || 0,
      countiesReporting: data.recent_anomalies ? 47 : 0,
      oneHealthSignals: Math.floor((data.national_compliance_index || 0) * 10),
      ...data
    };
  } catch (e) {
    return { totalIsolates: 0, activeAnomalies: 0, countiesReporting: 0, oneHealthSignals: 0 };
  }
};

export const fetchChoroplethData = async () => {
  try {
    const { data } = await apiClient.get('/intelligence/heatmap');
    return {
      type: 'FeatureCollection',
      features: data.map(item => ({
        type: 'Feature',
        properties: {
          county: item.location.county,
          resistanceRate: item.intensity_weight,
          riskLevel: item.intensity_weight > 0.5 ? 'high' : item.intensity_weight > 0.2 ? 'medium' : 'low'
        },
        geometry: { type: 'Point', coordinates: [item.location.longitude, item.location.latitude] }
      }))
    };
  } catch (e) {
    return { type: 'FeatureCollection', features: [] };
  }
};

export const fetchAlerts = async ({ queryKey }) => {
  try {
    const { data } = await apiClient.get('/intelligence/alerts');
    return data;
  } catch (e) {
    return [];
  }
};

export const fetchAlertDetail = async (alertId) => {
  try {
    const { data } = await apiClient.get(`/intelligence/alerts/${alertId}`);
    return data;
  } catch (e) {
    return null;
  }
};

export const fetchAlertExplanation = async (alertId) => {
  try {
    const { data } = await apiClient.get(`/intelligence/alerts/${alertId}/explanation`);
    return data;
  } catch (e) {
    return { plainTextSummary: "Explanation not available.", contributors: [] };
  }
};

export const fetchAlertGuidance = async ({ alertId, role }) => {
  try {
    const { data } = await apiClient.get(`/intelligence/alerts/${alertId}/guidance`, { params: { role } });
    return data;
  } catch (e) {
    return { summaryText: "Guidance not available.", recommendations: [], actionChecklist: [], references: [] };
  }
};

export const fetchTrends = async ({ queryKey }) => {
  const [, pathogen, drug, region, months] = queryKey;
  try {
    const { data } = await apiClient.get('/intelligence/trends', { params: { pathogen, drug, region, months } });
    return data;
  } catch (e) {
    return { series: [] };
  }
};