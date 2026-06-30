/**
 * api/client.js — AMR-Nexus Unified API Client v2.2
 *
 * Single source of truth for all backend communication.
 * - Vite proxy: /api → http://localhost:8080 (configured in vite.config.js)
 * - baseURL: /api/v1
 * - Auto-injects Authorization: Bearer <token> on every request
 * - 401 auto-logout: clears localStorage + redirects to /login
 * - All 27 backend endpoints mapped as named methods
 */

import axios from 'axios';

// ── Axios Instance ────────────────────────────────────────────────────────────

const axiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// ── Request Interceptor: Inject Bearer Token ──────────────────────────────────

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response Interceptor: 401 Auto-Logout ────────────────────────────────────

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      // Avoid redirect loop on login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Helper: Build query string from object ────────────────────────────────────

const buildQuery = (params = {}) => {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== '')
  );
  const qs = new URLSearchParams(clean).toString();
  return qs ? `?${qs}` : '';
};

// ── API Methods ───────────────────────────────────────────────────────────────

export const api = {

  // ── Auth ────────────────────────────────────────────────────────────────────

  /**
   * POST /auth/token
   * Params: URLSearchParams with grant_type, username, password
   * Returns: { access_token, token_type }
   */
  login: (formData) =>
    axiosInstance.post('/auth/token', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  /**
   * POST /auth/register
   * Body: { username, name, email, password, role, county }
   * Returns: { message }
   */
  register: (data) => axiosInstance.post('/auth/register', data),

  // ── User Profile ────────────────────────────────────────────────────────────

  /**
   * GET /users/me
   * Returns: { username, name, email, role, county, is_active }
   */
  getMe: () => axiosInstance.get('/users/me'),

  /**
   * PUT /users/me
   * Body: { name?, email? }
   * Returns: { username, name, email, role, county, is_active }
   */
  updateMe: (data) => axiosInstance.put('/users/me', data),

  /**
   * GET /users/me/preferences
   * Returns: { anomaly_alerts, high_mdr_alerts, weekly_report, retention_days, report_format, report_schedule }
   */
  getPreferences: () => axiosInstance.get('/users/me/preferences'),

  /**
   * PUT /users/me/preferences
   * Body: { anomaly_alerts, high_mdr_alerts, weekly_report, retention_days, report_format, report_schedule }
   */
  updatePreferences: (data) => axiosInstance.put('/users/me/preferences', data),

  // ── Analytics / Intelligence ────────────────────────────────────────────────

  /**
   * GET /analytics/summary
   * Returns FLAT object: { total_isolates_scanned, active_hotspots_detected,
   *   national_compliance_index, resistance_breakdown, recent_anomalies[],
   *   top_resistant_pathogens[], last_updated, total_records, mdr_rate,
   *   anomaly_count, active_hotspots, compliance_index, active_counties }
   */
  getSummary: (params = {}) =>
    axiosInstance.get(`/analytics/summary${buildQuery(params)}`),

  /**
   * GET /analytics/mdr_trend?months=12&forecast=false&county=...
   * Returns: { series: [ { date, resistance_rate, anomaly_flag, forecast } ] }
   * NOTE: Unwrap with res.data.series
   */
  getMDRTrend: (months = 12, params = {}) =>
    axiosInstance.get(`/analytics/mdr_trend${buildQuery({ months, ...params })}`),

  /**
   * GET /analytics/by_pathogen?limit=10
   * Returns: { status: "success", data: [ { pathogen_name, count } ] }
   * NOTE: Unwrap with res.data.data
   */
  getByPathogen: (limit = 10) =>
    axiosInstance.get(`/analytics/by_pathogen${buildQuery({ limit })}`),

  /**
   * GET /intelligence/heatmap?county=...&sector=...&limit=500
   * Returns FLAT array: [ { location: {county, sub_county, latitude, longitude},
   *   intensity_weight, pathogen_profile, resistance_level, classification,
   *   resistance_percent, sector, sample_count } ]
   */
  getHeatmapCoordinates: (params = {}) =>
    axiosInstance.get(`/intelligence/heatmap${buildQuery(params)}`),

  /**
   * GET /intelligence/risk-summary
   * Returns: { total_alerts, avg_anomaly_score, max_hotspot_magnitude,
   *   critical_count, high_count, medium_count, top_risk_counties[] }
   */
  getRiskSummary: () => axiosInstance.get('/intelligence/risk-summary'),

  // ── Alerts ──────────────────────────────────────────────────────────────────

  /**
   * GET /alerts?role=...&county=...
   * Returns FLAT array: [ { id, pathogen, drug_class, county, sub_county,
   *   risk_score, summary, triggered_at, anomaly_type, status, sector,
   *   antibiotic_name, anomaly_score } ]
   */
  getAlerts: (params = {}) =>
    axiosInstance.get(`/alerts${buildQuery(params)}`),

  /**
   * GET /intelligence/alerts/{alert_id}
   * Returns single alert object (same fields as list item)
   */
  getAlertDetail: (alertId) =>
    axiosInstance.get(`/intelligence/alerts/${alertId}`),

  /**
   * GET /intelligence/alerts/{alert_id}/explanation
   * Returns: { plain_text_summary, contributors: [{ factor, contribution_percent }] }
   */
  getAlertExplanation: (alertId) =>
    axiosInstance.get(`/intelligence/alerts/${alertId}/explanation`),

  /**
   * GET /intelligence/alerts/{alert_id}/guidance?role=...
   * Returns: { summary_text, recommendations[], action_checklist[], references[] }
   */
  getAlertGuidance: (alertId, role) =>
    axiosInstance.get(`/intelligence/alerts/${alertId}/guidance${buildQuery({ role })}`),

  // ── Records / Predictions ───────────────────────────────────────────────────

  /**
   * GET /predictions?limit=50&skip=0&county=...&pathogen_name=...&sir_result=...&sector=...
   * Returns FLAT array of AMR record objects
   */
  getPredictions: (limit = 50, skip = 0, params = {}) =>
    axiosInstance.get(`/predictions${buildQuery({ limit, skip, ...params })}`),

  /**
   * GET /records/{record_id}
   * Returns full AMR record with all fields
   */
  getRecord: (recordId) => axiosInstance.get(`/records/${recordId}`),

  /**
   * DELETE /records/{record_id}
   * Returns: { status, record_id, deleted_at }
   */
  deleteRecord: (recordId) => axiosInstance.delete(`/records/${recordId}`),

  /**
   * POST /records/bulk/
   * Body: array of AMRRecordCreate objects (up to 10,000)
   * Returns: { status, processed_records, failed_critical, record_ids[], task_queued, message }
   */
  bulkIngest: (records) => axiosInstance.post('/records/bulk/', records),

  // ── Reports ─────────────────────────────────────────────────────────────────

  /**
   * POST /reports/schedule
   * Body: { email, format: "pdf"|"csv"|"xlsx", type: "weekly"|"monthly"|"custom", schedule }
   * Returns: { status, report_id, email, format, type, schedule, created_at }
   */
  scheduleReport: (data) => axiosInstance.post('/reports/schedule', data),

  /**
   * GET /reports/schedule
   * Returns FLAT array: [ { report_id, email, format, type, schedule, status, created_at } ]
   */
  getScheduledReports: () => axiosInstance.get('/reports/schedule'),

  // ── Decision Support ─────────────────────────────────────────────────────────

  /**
   * POST /decision-support/{record_id}
   * Returns: { record_id, status, task_id, guidance, role_target, generated_at }
   */
  triggerDecisionSupport: (recordId) =>
    axiosInstance.post(`/decision-support/${recordId}`),

  /**
   * GET /decision-support/{record_id}
   * Returns: { record_id, status, task_id, guidance, role_target, generated_at }
   */
  getDecisionSupport: (recordId) =>
    axiosInstance.get(`/decision-support/${recordId}`),

  // ── Health ──────────────────────────────────────────────────────────────────

  /**
   * GET /health  (no /api/v1 prefix — raw endpoint)
   * Returns: { status: "healthy", service, version }
   */
  health: () => axios.get('/health'),

  // ── Convenience helpers (no dedicated backend route) ─────────────────────────

  /**
   * getTopCounties(limit)
   * Derives top counties from GET /intelligence/risk-summary → top_risk_counties[]
   * Returns Axios response whose .data is an array of { county, avg_score, alert_count }
   */
  getTopCounties: async (limit = 5) => {
    const res = await axiosInstance.get('/intelligence/risk-summary');
    const counties = Array.isArray(res.data?.top_risk_counties)
      ? res.data.top_risk_counties.slice(0, limit)
      : [];
    // Normalize shape: add .county and .rate for TopCounties component
    const normalised = counties.map(c => ({
      county:      c.county,
      rate:        parseFloat((c.avg_score * 100).toFixed(1)),
      alert_count: c.alert_count,
    }));
    return { ...res, data: normalised };
  },

  /**
   * getBySector(params)
   * Aggregates sector breakdown from GET /intelligence/heatmap
   * Returns Axios response whose .data is an array of { sector, count }
   */
  getBySector: async (params = {}) => {
    const res = await axiosInstance.get(`/intelligence/heatmap${buildQuery({ ...params, limit: 1000 })}`);
    const rows = Array.isArray(res.data) ? res.data : [];
    const sectorMap = {};
    rows.forEach(pt => {
      const s = pt.sector ?? 'UNKNOWN';
      sectorMap[s] = (sectorMap[s] || 0) + 1;
    });
    const data = Object.entries(sectorMap).map(([sector, count]) => ({ sector, count }));
    return { ...res, data };
  },

  /**
   * submitPrediction(recordData)
   * Convenience wrapper: ingests a single AMR record via POST /records/bulk/
   * Returns the bulk ingest response.
   */
  submitPrediction: (recordData) =>
    axiosInstance.post('/records/bulk/', [recordData]),
};

export default api;