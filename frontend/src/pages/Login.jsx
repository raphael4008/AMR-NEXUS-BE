/**
 * Login.jsx — AMR-Nexus E2E Login + Registration Page v2.2
 *
 * Features:
 *  - Toggle between Login and Register modes
 *  - Login: POST /auth/token → GET /users/me → role-based redirect
 *  - Register: POST /auth/register with all 47 Kenya counties + 4 role options
 *  - Password visibility toggle
 *  - Inline validation errors
 *  - Rate-limit error display (429)
 *  - Glassmorphism premium UI
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';

// ── Kenya Counties (47) ────────────────────────────────────────────────────────
const KENYA_COUNTIES = [
  'Baringo','Bomet','Bungoma','Busia','Elgeyo-Marakwet','Embu','Garissa',
  'Homa Bay','Isiolo','Kajiado','Kakamega','Kericho','Kiambu','Kilifi',
  'Kirinyaga','Kisii','Kisumu','Kitui','Kwale','Laikipia','Lamu','Machakos',
  'Makueni','Mandera','Marsabit','Meru','Migori','Mombasa','Murang\'a',
  'Nairobi','Nakuru','Nandi','Narok','Nyamira','Nyandarua','Nyeri','Samburu',
  'Siaya','Taita-Taveta','Tana River','Tharaka-Nithi','Trans Nzoia','Turkana',
  'Uasin Gishu','Vihiga','Wajir','West Pokot',
];

// ── Registerable Roles (county staff only) ────────────────────────────────────
const REGISTER_ROLES = [
  { value: 'County Veterinarian', label: 'County Veterinarian (Animal Health)' },
  { value: 'County Clinician',    label: 'County Clinician (Human Health)' },
];

// ── Role → Dashboard Route Map ────────────────────────────────────────────────
const ROLE_ROUTES = {
  'National Coordinator':    '/national',
  'County Veterinarian':     '/county',
  'County Clinician':        '/county',
  'Policy Maker':            '/national',
  'Lab Technician':          '/county',
};

export default function Login() {
  const { login } = useAuth();
  const navigate   = useNavigate();

  // ── UI Mode ───────────────────────────────────────────────────────────────
  const [mode, setMode]         = useState('login'); // 'login' | 'register'
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const [showPass, setShowPass] = useState(false);

  // ── Login Form ─────────────────────────────────────────────────────────────
  const [loginForm, setLoginForm] = useState({ identifier: '', password: '' });

  // ── Register Form ──────────────────────────────────────────────────────────
  const [regForm, setRegForm] = useState({
    username: '',
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
    county: '',
  });

  // ── Switch Mode ───────────────────────────────────────────────────────────
  const switchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setSuccess('');
  };

  // ── Login Submit ──────────────────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login({
        identifier: loginForm.identifier.trim(),
        password:   loginForm.password,
      });
      // Role-based redirect
      const route = ROLE_ROUTES[user.role] ?? '/national';
      navigate(route, { replace: true });
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('Invalid username or password. Please try again.');
      } else if (status === 429) {
        setError('Too many login attempts. Please wait a minute and try again.');
      } else {
        setError('Unable to connect to the server. Check your network connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Register Submit ───────────────────────────────────────────────────────
  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Client-side validation
    if (regForm.password !== regForm.confirmPassword) {
      return setError('Passwords do not match.');
    }
    if (regForm.password.length < 8) {
      return setError('Password must be at least 8 characters.');
    }
    if (!regForm.role) {
      return setError('Please select your role.');
    }
    if (!regForm.county) {
      return setError('Please select your county.');
    }

    setLoading(true);
    try {
      await api.register({
        username: regForm.username.trim(),
        name:     regForm.name.trim(),
        email:    regForm.email.trim(),
        password: regForm.password,
        role:     regForm.role,
        county:   regForm.county,
      });
      setSuccess(
        'Account created successfully! Your account is pending admin activation. ' +
        'You will be notified by email when it is active.'
      );
      // Reset form and switch back to login after 3s
      setRegForm({ username: '', name: '', email: '', password: '', confirmPassword: '', role: '', county: '' });
      setTimeout(() => switchMode('login'), 3500);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 409) {
        setError(detail ?? 'Username or email already in use.');
      } else if (status === 400) {
        setError(detail ?? 'Invalid registration data. Please check your inputs.');
      } else if (status === 422) {
        setError(detail ?? 'Please fill in all required fields.');
      } else {
        setError('Registration failed. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 p-4">

      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-cyan-600/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">

        {/* Logo + Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 shadow-lg shadow-blue-600/40 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1 1 .3 2.7-1.1 2.7H3.9c-1.4 0-2.1-1.7-1.1-2.7l1.4-1.402" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">AMR‑Nexus</h1>
          <p className="text-blue-300 text-sm mt-1">One Health Antimicrobial Resistance Platform</p>
        </div>

        {/* Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">

          {/* Mode Tabs */}
          <div className="flex rounded-full bg-white/10 p-1 mb-6">
            <button
              onClick={() => switchMode('login')}
              className={`flex-1 py-2 rounded-full text-sm font-medium transition-all ${
                mode === 'login'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => switchMode('register')}
              className={`flex-1 py-2 rounded-full text-sm font-medium transition-all ${
                mode === 'register'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Register
            </button>
          </div>

          {/* ── SUCCESS BANNER ───────────────────────────────────────────── */}
          {success && (
            <div className="mb-4 p-4 bg-green-500/20 border border-green-400/40 rounded-2xl text-green-300 text-sm flex gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
              </svg>
              {success}
            </div>
          )}

          {/* ── ERROR BANNER ─────────────────────────────────────────────── */}
          {error && (
            <div className="mb-4 p-4 bg-red-500/20 border border-red-400/40 rounded-2xl text-red-300 text-sm flex gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
              </svg>
              {error}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════════ */}
          {/* LOGIN FORM                                                    */}
          {/* ══════════════════════════════════════════════════════════════ */}
          {mode === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">

              {/* Username / Email */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Username or Email</label>
                <input
                  id="login-identifier"
                  type="text"
                  autoComplete="username"
                  required
                  value={loginForm.identifier}
                  onChange={(e) => setLoginForm({ ...loginForm, identifier: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  placeholder="admin or admin@amrnexus.org"
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPass ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 pr-12 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition"
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                  >
                    {showPass ? (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0 1 12 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 0 1 1.563-3.029m5.858.908a3 3 0 1 1 4.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532 3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0 1 12 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 0 1-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Signing in…
                  </>
                ) : 'Sign In'}
              </button>

              {/* Role hint */}
              <p className="text-xs text-blue-300 text-center">
                National Coordinator / Policy Maker / County Clinician / County Vet
              </p>
            </form>
          )}

          {/* ══════════════════════════════════════════════════════════════ */}
          {/* REGISTER FORM                                                 */}
          {/* ══════════════════════════════════════════════════════════════ */}
          {mode === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">

              {/* Full Name */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Full Name</label>
                <input
                  id="reg-name"
                  type="text"
                  required
                  value={regForm.name}
                  onChange={(e) => setRegForm({ ...regForm, name: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  placeholder="Dr. Jane Mwangi"
                />
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Username</label>
                <input
                  id="reg-username"
                  type="text"
                  autoComplete="username"
                  required
                  value={regForm.username}
                  onChange={(e) => setRegForm({ ...regForm, username: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  placeholder="dr.jane.mwangi"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Work Email</label>
                <input
                  id="reg-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={regForm.email}
                  onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  placeholder="jane@health.go.ke"
                />
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Role</label>
                <select
                  id="reg-role"
                  required
                  value={regForm.role}
                  onChange={(e) => setRegForm({ ...regForm, role: e.target.value })}
                  className="w-full bg-slate-800 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                >
                  <option value="">Select your role…</option>
                  {REGISTER_ROLES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              {/* County */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">County</label>
                <select
                  id="reg-county"
                  required
                  value={regForm.county}
                  onChange={(e) => setRegForm({ ...regForm, county: e.target.value })}
                  className="w-full bg-slate-800 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                >
                  <option value="">Select your county…</option>
                  {KENYA_COUNTIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    id="reg-password"
                    type={showPass ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={regForm.password}
                    onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 pr-12 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    placeholder="Min. 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition"
                  >
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm text-blue-200 mb-1.5">Confirm Password</label>
                <input
                  id="reg-confirm-password"
                  type={showPass ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={regForm.confirmPassword}
                  onChange={(e) => setRegForm({ ...regForm, confirmPassword: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  placeholder="Re-enter password"
                />
              </div>

              {/* Terms note */}
              <p className="text-xs text-blue-300">
                New accounts require admin approval. You will receive an email when your account is activated.
                Self-registration is limited to County Veterinarians and County Clinicians.
              </p>

              {/* Submit */}
              <button
                id="register-submit"
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Registering…
                  </>
                ) : 'Create Account'}
              </button>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-blue-400/60 text-xs mt-6">
          AMR‑Nexus One Health Platform · Kenya © {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}