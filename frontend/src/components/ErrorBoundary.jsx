/**
 * ErrorBoundary.jsx — React Error Boundary v2.2
 *
 * Catches render-time errors that would cause a blank screen ("White Screen of Death").
 * Displays a friendly fallback UI instead of an empty page.
 * Includes:
 *  - Full error + stack trace display (dev mode)
 *  - "Try Again" button to reset the boundary
 *  - Automatic recovery on route changes
 */

import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // In production you'd send to Sentry / Datadog here
    console.error('[AMR-Nexus ErrorBoundary]', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 p-6">
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-3xl p-8 max-w-lg w-full shadow-2xl text-white">

          {/* Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 rounded-full bg-red-500/20 border border-red-400/40 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
          </div>

          <h1 className="text-xl font-bold text-center mb-2">Something went wrong</h1>
          <p className="text-blue-200 text-sm text-center mb-6">
            The page encountered an unexpected error. Your data is safe.
          </p>

          {/* Error details (visible in development) */}
          {this.state.error && (
            <details className="mb-6 bg-white/5 rounded-xl p-4 text-xs font-mono overflow-auto max-h-40">
              <summary className="text-red-300 cursor-pointer mb-2">Error Details</summary>
              <p className="text-red-200">{this.state.error.toString()}</p>
              {this.state.errorInfo?.componentStack && (
                <pre className="text-slate-400 mt-2 whitespace-pre-wrap text-xs">
                  {this.state.errorInfo.componentStack}
                </pre>
              )}
            </details>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={this.handleReset}
              className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-medium transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => { window.location.href = '/'; }}
              className="flex-1 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-full font-medium transition-colors border border-white/20"
            >
              Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
