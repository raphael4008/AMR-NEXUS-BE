const API_BASE = 'http://localhost:8000';

async function handleResponse(res) {
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorMessage;
    } catch { }
    throw new Error(errorMessage);
  }
  return res.json();
}

export const api = {
  health: () => fetch(`${API_BASE}/health`).then(handleResponse),
  getSummary: (params = '') => fetch(`${API_BASE}/analytics/summary?${params}`).then(handleResponse),
  getMDRTrend: (months = 6, params = '') => fetch(`${API_BASE}/analytics/mdr_trend?months=${months}&${params}`).then(handleResponse),
  getByPathogen: (limit = 10, params = '') => fetch(`${API_BASE}/analytics/by_pathogen?limit=${limit}&${params}`).then(handleResponse),
  getBySector: (params = '') => fetch(`${API_BASE}/analytics/by_sector?${params}`).then(handleResponse),
  getBySectorTrend: (params = '') => fetch(`${API_BASE}/analytics/by_sector_trend?${params}`).then(handleResponse),
  getTopCounties: (limit = 5, params = '') => fetch(`${API_BASE}/analytics/top_counties?limit=${limit}&${params}`).then(handleResponse),
  getPredictions: (limit = 50, skip = 0, params = '') => fetch(`${API_BASE}/predictions?limit=${limit}&skip=${skip}&${params}`).then(handleResponse),
  submitPrediction: (data) => fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  getCountyMDR: (params = '') => fetch(`${API_BASE}/analytics/county_mdr?${params}`).then(handleResponse),
  emailReport: (data) => fetch(`${API_BASE}/reports/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  getComments: (recordId) => fetch(`${API_BASE}/predictions/${recordId}/comments`).then(handleResponse),
  addComment: (recordId, data) => fetch(`${API_BASE}/predictions/${recordId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  getForecast: (params = '') => fetch(`${API_BASE}/ews/forecast?${params}`).then(handleResponse),
  getRecommendations: (pathogen, antibioticClass) => fetch(`${API_BASE}/recommendations/${pathogen}/${antibioticClass}`).then(handleResponse),
  getMe: () => fetch(`${API_BASE}/me`).then(handleResponse),
  getAlerts: (params = '') => fetch(`${API_BASE}/alerts?${params}`).then(handleResponse),
  getAlertsCount: () => fetch(`${API_BASE}/alerts/count`).then(handleResponse),
  getOptions: () => fetch(`${API_BASE}/metadata/options`).then(handleResponse),
  updatePredictionNote: (recordId, data) => fetch(`${API_BASE}/predictions/${recordId}/note`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  getTemplates: () => fetch(`${API_BASE}/templates`).then(handleResponse),
  saveTemplate: (name, formData) => fetch(`${API_BASE}/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, form_data: formData })
  }).then(handleResponse),
  deleteTemplate: (id) => fetch(`${API_BASE}/templates/${id}`, {
    method: 'DELETE'
  }).then(handleResponse),
  markAlertRead: (id) => fetch(`${API_BASE}/alerts/${id}/read`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
  }).then(handleResponse),
};

export default api;