import { Link, useLocation } from 'react-router-dom';

export default function Breadcrumbs() {
  const location = useLocation();
  const paths = location.pathname.split('/').filter(p => p);
  if (paths.length === 0) return null;

  const titles = {
    predict: 'Predict',
    analytics: 'Analytics',
    history: 'History',
    alerts: 'Alerts',
    reports: 'Reports',
    settings: 'Settings',
    compare: 'Compare',
    'pathogen-explorer': 'Pathogen Explorer',
    'bulk-import': 'Bulk Import',
    'compare-analytics': 'Compare Analytics',
    'data-quality': 'Data Quality',
  };

  return (
    <div className="hidden md:flex items-center text-sm text-gray-500 ml-4">
      {paths.map((p, idx) => (
        <div key={p} className="flex items-center">
          {idx > 0 && <span className="mx-2">/</span>}
          <Link to={`/${paths.slice(0, idx+1).join('/')}`} className="hover:text-primary-600">
            {titles[p] || p}
          </Link>
        </div>
      ))}
    </div>
  );
}