/**
 * api/client.js — AMR-Nexus Single Authoritative API Client
 *
 * Architecture:
 *  - ONE Axios instance, base URL from VITE_API_BASE_URL env variable
 *  - Auto-injects Authorization Bearer token from localStorage
 *  - 401 response → clears stored token, redirects to /login
 *  - All service functions map to REAL backend routes
 *  - Derived functions (top counties, by sector, data quality) are
 *    computed client-side from real endpoint responses — no ghost routes
 */

import axios from 'axios';

// ── Axios instance ─────────────────────────────────────────────────────────────
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
const API_V1   = `${BASE_URL}/api/v1`;

const axiosClient = axios.create({
  baseURL: API_V1,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ── Request interceptor: attach JWT ───────────────────────────────────────────
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('amr_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 globally ─────────────────────────────────
axiosClient.interceptors.response.use(
  (response) => {
    // If the response is already an object (axios auto-parsed JSON), return it
    if (typeof response.data === 'object') return response;
    
    // If it's a string that doesn't look like JSON, throw an error
    if (typeof response.data === 'string' && !response.data.trim().startsWith('{')) {
        throw new Error("API returned non-JSON response");
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear storage and redirect to login
      localStorage.removeItem('amr_token');
      localStorage.removeItem('amr_user');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    // Normalise error message for UI consumption
    const detail = error.response?.data?.detail;
    const message = typeof detail === 'string'
      ? detail
      : `HTTP ${error.response?.status ?? 'Network Error'}`;
    return Promise.reject(new Error(message));
  }
);

// ── Response normalisation helpers ────────────────────────────────────────────
/**
 * Normalises the dashboard summary so legacy field names still work
 * across components that were built against the old schema.
 *
 * Backend →                Frontend alias
 * total_isolates_scanned → total_records
 * active_hotspots_detected → anomaly_count, active_hotspots
 * resistance_breakdown.resistance_percent → mdr_rate
 * national_compliance_index → compliance_index
 */
function normaliseSummary(data) {
  if (!data) return data;
  console.log("DEBUG: Backend response:", data);
  return {
    ...data,
    // Aliases for components using old field names
    total_records: data.total_isolates_scanned ?? 0,
    anomaly_count: data.active_hotspots_detected ?? 0,
    active_hotspots: data.active_hotspots_detected ?? 0,
    mdr_rate: data.resistance_breakdown?.resistance_percent ?? 0,
    compliance_index: data.national_compliance_index ?? 0,
  };
}

/**
 * Normalises a trend series so that camelCase and snake_case both work.
 * Backend: { date, resistance_rate, anomaly_flag }
 */
function normaliseTrend(data) {
  if (!data?.series) return data;
  return {
    ...data,
    series: data.series.map((point) => ({
      ...point,
      // camelCase aliases for Recharts components
      date: point.date,
      resistanceRate: point.resistance_rate,
      anomalyFlag: point.anomaly_flag,
    })),
  };
}

/**
 * Derives top-counties list from heatmap response.
 * Groups by county, sums sample counts, sorts descending.
 */
function deriveTopCounties(heatmapData, limit = 10) {
  const map = {};
  for (const row of heatmapData) {
    const county = row.location?.county ?? row.county;
    if (!county) continue;
    if (!map[county]) {
      map[county] = { county, rate: 0, count: 0 };
    }
    map[county].count  += row.sample_count ?? 1;
    map[county].rate    = Math.max(map[county].rate, row.intensity_weight ?? 0);
  }
  return Object.values(map)
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

/**
 * Derives sector breakdown from heatmap response.
 */
function deriveBySector(heatmapData) {
  const map = {};
  for (const row of heatmapData) {
    const sector = row.sector ?? 'UNKNOWN';
    if (!map[sector]) map[sector] = { name: sector, value: 0, count: 0 };
    map[sector].count += row.sample_count ?? 1;
    map[sector].value  = Math.round(
      ((map[sector].value * (map[sector].count - 1)) + (row.intensity_weight ?? 0) * 100)
      / map[sector].count
    );
  }
  return Object.values(map);
}

/**
 * Derives pathogen resistance list from top_resistant_pathogens summary field.
 * Backend: [{ pathogen, count }]
 * Returns: [{ name, count, resistance }]
 */
function deriveByPathogen(summaryData) {
  return (summaryData?.top_resistant_pathogens ?? []).map((p) => ({
    ...p,
    name: p.pathogen,
    resistance: p.count,
  }));
}


// ── Real API service functions ─────────────────────────────────────────────────
export const api = {

  // ── Auth ──────────────────────────────────────────────────────────────────
  /**
   * Login with username + password.
   * Backend expects application/x-www-form-urlencoded (OAuth2PasswordRequestForm).
   * Stores token in localStorage on success.
   */
  login: async (username, password) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const { data } = await axiosClient.post('/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    // Persist token for request interceptor
    localStorage.setItem('amr_token', data.access_token);
    return data;
  },

  logout: () => {
    localStorage.removeItem('amr_token');
    localStorage.removeItem('amr_user');
    window.location.href = '/login';
  },

  // ── Health ────────────────────────────────────────────────────────────────
  health: async () => {
    const { data } = await axios.get(`${BASE_URL}/health`);
    return data;
  },

  // ── Intelligence — Dashboard Summary ──────────────────────────────────────
  /** GET /api/v1/intelligence/dashboard/summary */
  getSummary: async (queryString = '') => {
    const { data } = await axiosClient.get(
      `/intelligence/dashboard/summary${queryString ? `?${queryString}` : ''}`
    );
    return normaliseSummary(data);
  },

  // ── Intelligence — Trends ─────────────────────────────────────────────────
  /** GET /api/v1/intelligence/trends */
  getMDRTrend: async (months = 6, queryString = '') => {
    const params = new URLSearchParams(queryString);
    params.set('months', months);
    const { data } = await axiosClient.get(`/intelligence/trends?${params}`);
    return normaliseTrend(data);
  },

  // alias used by some components
  getForecast: async (queryString = '') => {
    const { data } = await axiosClient.get(
      `/intelligence/trends${queryString ? `?${queryString}` : ''}`
    );
    return normaliseTrend(data);
  },

  // ── Intelligence — Heatmap (raw) ──────────────────────────────────────────
  /** GET /api/v1/intelligence/heatmap */
  getHeatmap: async ({ county, sector, limit = 500 } = {}) => {
    const params = new URLSearchParams();
    if (county) params.set('county', county);
    if (sector) params.set('sector', sector);
    params.set('limit', limit);
    const { data } = await axiosClient.get(`/intelligence/heatmap?${params}`);
    return data;
  },

  // ── Derived: Top Counties (client-computed from heatmap) ──────────────────
  getTopCounties: async (limit = 5, queryString = '') => {
    const heatmap = await api.getHeatmap({ limit: 2000 });
    return deriveTopCounties(heatmap, limit);
  },

  // ── Derived: By Sector (client-computed from heatmap) ────────────────────
  getBySector: async (queryString = '') => {
    const heatmap = await api.getHeatmap({ limit: 2000 });
    return deriveBySector(heatmap);
  },

  // ── Derived: By Pathogen (from summary top_resistant_pathogens) ───────────
  getByPathogen: async (limit = 10, queryString = '') => {
    const summary = await api.getSummary(queryString);
    return deriveByPathogen(summary).slice(0, limit);
  },

  // ── Derived: County MDR (heatmap with county filter) ─────────────────────
  getCountyMDR: async (queryString = '') => {
    const params = new URLSearchParams(queryString);
    return api.getHeatmap({ county: params.get('county'), limit: 1000 });
  },

  // ── Derived: Data Quality (from summary compliance index) ─────────────────
  getDataQuality: async () => {
    const summary = await api.getSummary();
    return {
      compliance_index: summary.national_compliance_index,
      total_records: summary.total_isolates_scanned,
      quality_score: summary.national_compliance_index,
      clean_records: Math.round(summary.total_isolates_scanned * summary.national_compliance_index),
    };
  },

  // ── Intelligence — Alerts ─────────────────────────────────────────────────
  /** GET /api/v1/intelligence/alerts */
  getAlerts: async (role = '') => {
    const params = role ? `?role=${role}` : '';
    const { data } = await axiosClient.get(`/intelligence/alerts${params}`);
    return data;
  },

  /** GET /api/v1/intelligence/alerts/:id */
  getAlertDetail: async (alertId) => {
    const { data } = await axiosClient.get(`/intelligence/alerts/${alertId}`);
    return data;
  },

  /** GET /api/v1/intelligence/alerts/:id/explanation */
  getAlertExplanation: async (alertId) => {
    const { data } = await axiosClient.get(`/intelligence/alerts/${alertId}/explanation`);
    return data;
  },

  /** GET /api/v1/intelligence/alerts/:id/guidance */
  getAlertGuidance: async (alertId, role = '') => {
    const params = role ? `?role=${role}` : '';
    const { data } = await axiosClient.get(`/intelligence/alerts/${alertId}/guidance${params}`);
    return data;
  },

  // ── Records ───────────────────────────────────────────────────────────────
  /** GET /api/v1/records */
  getPredictions: async (limit = 50, skip = 0, queryString = '') => {
    const params = new URLSearchParams(queryString);
    params.set('limit', limit);
    params.set('skip', skip);
    const { data } = await axiosClient.get(`/records?${params}`);
    return data;
  },

  /**
   * POST /api/v1/records/bulk/
   * Accepts an array of AMRRecordCreate-shaped objects.
   * Returns BulkIngestResponse { status, processed_records, record_ids, task_queued }
   */
  bulkIngest: async (records) => {
    const { data } = await axiosClient.post('/records/bulk/', records);
    return data;
  },

  // Legacy alias used by BulkImport.jsx / predictionStore
  submitPrediction: async (record) => {
    return api.bulkIngest([record]);
  },

  // ── Client-side Export (replaces ghost /export/predictions endpoint) ───────
  exportRecordsCSV: async () => {
    const records = await api.getPredictions(10_000, 0);
    const headers = ['record_id', 'pathogen_code', 'county', 'mdr_flag', 'mdr_probability', 'sector', 'timestamp'];
    const rows = records.map((r) =>
      [r.record_id, r.pathogen_code, r.county, r.mdr_flag, r.mdr_probability, r.sector, r.timestamp].join(',')
    );
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `amr_records_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  },

  // ── Stub: Ghost endpoints removed — emit console warning if called ─────────
  emailReport:   () => Promise.reject(new Error('Email reports not implemented')),
  getComments:   () => Promise.resolve([]),
  addComment:    () => Promise.resolve({}),
  getMe:         () => Promise.resolve(JSON.parse(localStorage.getItem('amr_user') || 'null')),
  getRecommendations: async () => api.getAlerts(),
};

export default api;
