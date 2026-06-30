/**
 * hooks/useAuth.js — Thin re-export of AuthContext
 *
 * FIXED: Previously contained a hardcoded mock user { name: 'John Doe' }
 * and an incomplete logout that only removed 'user' from localStorage
 * (leaving the auth token behind, so the session persisted after logout).
 *
 * Now simply re-exports from AuthContext so ALL components share one
 * consistent auth state regardless of which import path they use.
 */

export { useAuth } from '../contexts/AuthContext';